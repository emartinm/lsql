"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Unit tests for the validation of statements using DES
"""

from django.core.exceptions import ValidationError
from django.test import TestCase
from judge.des_driver import parse_tapi_cmd, DesExecutor, parse_tapi_commands, filter_unrecognized_start_of_input
from judge.exceptions import DESException
from judge.models import SelectProblem, DMLProblem
from judge.types import DesMessageType


class DesTest(TestCase):
    """ Tests for des_driver """
    __CREATE_TIMEOUT = """
CREATE TABLE jugadores (
  nick STRING PRIMARY KEY,
  edad INTEGER CHECK (edad>0),
  ciudad STRING);

CREATE TABLE juegos (
  nombre STRING PRIMARY KEY,
  tipo STRING CHECK (tipo IN ('puzzle','estrategia','plataformas')),
  niveles INTEGER CHECK (niveles BETWEEN 1 AND 10));

CREATE TABLE partidas (
  juego STRING REFERENCES juegos(nombre),
  nick STRING REFERENCES jugadores(nick),
  nivel INTEGER CHECK (nivel BETWEEN 1 AND 10),
  superado STRING CHECK (superado IN ('S', 'N')),
  tiempo NUMBER(8,1) CHECK (tiempo>0),
  PRIMARY KEY (juego, nick, nivel));
  
CREATE VIEW v4 AS (SELECT DISTINCT nick, edad, ciudad FROM partidas NATURAL JOIN jugadores, (SELECT MAX(edad) as maximo FROM (SELECT nick, edad, ciudad FROM partidas NATURAL JOIN jugadores WHERE juego = 'Tetris')) WHERE edad = maximo and juego = 'Tetris')

CREATE VIEW v6 AS (SELECT nick FROM (SELECT * FROM partidas) DIVISION (SELECT juego FROM partidas WHERE juego = 'Tetris'));"""
    __QUERY_TIMEOUT = ''

    def test_parsing_wrong_des_output(self):
        """ Test some erroneous DES output (wrong $erroro) """
        output = """$erroro
0
Unknown table 'Jugador'.
$error
1
Some warning
with several lines
$error
1
Info message
second line
even a third one
$eot
"""
        with self.assertRaises(DESException) as ctx:
            parse_tapi_cmd(output, 0)
        self.assertIn('<$erroro>', str(ctx.exception))

    def test_parsing_des_output(self):
        """ Test the different kinds of error messages in DES output """
        output = """$error
0
Unknown table 'Jugador'.
$error
1
Some warning
with several lines
$error
2
Info message
second line
$
snippet
$eot
"""
        des_messages = parse_tapi_cmd(output, 0)
        self.assertEqual(des_messages[1],
                         [(DesMessageType.ERROR, "Unknown table 'Jugador'.", None),
                          (DesMessageType.WARNING, 'Some warning\nwith several lines', None),
                          (DesMessageType.INFO, 'Info message\nsecond line', 'snippet\n')]
                         )

        # Successful messages
        for output in ['$success\n', '1\n', '5\n', '$eot\n']:
            self.assertEqual(parse_tapi_cmd(output, 0)[1], [])

    def test_messages_query(self):
        """ Test that messages are empty in a correct submission """
        create = "CREATE TABLE t(age INT);"
        insert = "INSERT INTO t VALUES (5);\nINSERT INTO t VALUES (55);"
        query = "SELECT * FROM t;"
        msgs = list(DesExecutor.get().get_des_messages_select(create, insert, query))
        self.assertEqual(len(msgs), 4)
        for _, msg in msgs:
            self.assertEqual(msg, [])

    def test_messages_unsafe_select(self):
        """ Test that messages are empty in unsafe submissions """
        create = "CREATE TABLE t(age INT);"
        insert = "INSERT INTO t VALUES (5);\nINSERT INTO t VALUES (55);"
        query = "SELECT * FROM Club;"
        unsafe = "\\pwd"
        msgs = list(DesExecutor.get().get_des_messages_select(create, insert, unsafe))
        self.assertEqual(len(msgs), 0)
        msgs = list(DesExecutor.get().get_des_messages_select(create, unsafe, query))
        self.assertEqual(len(msgs), 0)
        msgs = list(DesExecutor.get().get_des_messages_select(unsafe, insert, query))
        self.assertEqual(len(msgs), 0)

    def test_des_timeout_select(self):
        """ DES require too much time to process SQL query, so it is aborted and raises DESException """
        with self.assertRaises(DESException) as ctx:
            DesExecutor.get().get_des_messages_select(self.__CREATE_TIMEOUT, '', self.__QUERY_TIMEOUT)
        self.assertIn("Timeout when invoking DES", str(ctx.exception))

    def test_des_timeout_problem_select(self):
        """ DES require too much time to process SQL query, so it is aborted and returns [] """
        problem = SelectProblem(create_sql=self.__CREATE_TIMEOUT, solution='SELECT * FROM Persona')
        msgs = problem.get_des_messages_solution(self.__QUERY_TIMEOUT)
        self.assertEqual(msgs, [])

    def test_validate_correct_problem(self):
        """ Test to validate with DES a correct SelectProblem """
        problem = SelectProblem(create_sql='CREATE TABLE t(age int)',
                                insert_sql='',
                                solution='SELECT * FROM t')
        self.assertIsNone(problem.validate_des())

    def test_validate_wrong_problem(self):
        """ Test to validate with DES a wrong SelectProblem """
        problem = SelectProblem(create_sql='CREATE TABLE t(age int);',
                                insert_sql='',
                                solution='SELECT * FROM table;')
        with self.assertRaises(ValidationError) as ctx:
            problem.validate_des()
        self.assertIn("Unknown table or view 'table'", ctx.exception.message)

    def test_dml(self):
        """ Checks that messages are empty in correct statements and DES messages errors are correctly detected
            in erroneous statements
        """
        create = "CREATE TABLE t(name VARCHAR(20) primary key, age INT);"
        insert = "INSERT INTO t VALUES ('pepe', 30);\nINSERT INTO t VALUES ('eve', 25);"
        dml1 = "UPDATE t SET age = 45;\n DELETE FROM t WHERE name = 'pepe';\n INSERT INTO t VALUES ('eve', 44);"
        dml2 = "INSERT INTO t VALUES ('eve', 67);"
        dml3 = """UPDATE t
        SET age = age + 1
        WHERE name = 'pepa'"""
        dml4 = """UPDATE t
        SET age = 45
        WHERE name = 'pepa';
        
        DELETE FROM t 
        WHERE name = 'pepa';
        
            INSERT INTO t 
            VALUES ('eve', 44);"""

        msgs = list(DesExecutor.get().get_des_messages_dml(create, insert, dml1))
        self.assertEqual(len(msgs), 6)
        # All statements are OK wrt. DES but the last one
        for _, msg in msgs[:-1]:
            self.assertEqual(msg, [])
        # The last statement produces 1 DES message with error of duplicate primary key and an empty snippet
        self.assertEqual(len(msgs[-1][1]), 1)
        self.assertEqual(msgs[-1][1][0][0], DesMessageType.ERROR)
        self.assertIn('Primary key violation', msgs[-1][1][0][1])
        self.assertIsNone(msgs[-1][1][0][2])

        msgs = list(DesExecutor.get().get_des_messages_dml(create, insert, dml2))
        self.assertEqual(len(msgs), 4)
        # All statements are OK wrt. DES but the last one
        for _, msg in msgs[:-1]:
            self.assertEqual(msg, [])
        # The last statement produces 1 DES message with error of duplicate primary key and an empty snippet
        self.assertEqual(len(msgs[-1][1]), 1)
        self.assertEqual(msgs[-1][1][0][0], DesMessageType.ERROR)
        self.assertIn('Primary key violation', msgs[-1][1][0][1])
        self.assertIsNone(msgs[-1][1][0][2])

        msgs = list(DesExecutor.get().get_des_messages_dml(create, insert, dml3))
        self.assertEqual(len(msgs), 4)
        # All statements are OK wrt. DES but the last one
        for _, msg in msgs[:-1]:
            self.assertEqual(msg, [])
        # The last statement produces 1 DES message with error of duplicate primary key and an empty snippet
        self.assertEqual(len(msgs[-1][1]), 1)
        self.assertEqual(msgs[-1][1][0][0], DesMessageType.WARNING)
        self.assertIn("No tuple met the 'where' condition for updating", msgs[-1][1][0][1])
        self.assertIsNone(msgs[-1][1][0][2])

        msgs = list(DesExecutor.get().get_des_messages_dml(create, insert, dml4))
        self.assertEqual(len(msgs), 6)
        # All statements are OK wrt. DES but the last one
        for _, msg in msgs[:-3]:
            self.assertEqual(msg, [])
        # The first DML statement statement produces 1 DES message (warning)
        self.assertEqual(len(msgs[-3][1]), 1)
        self.assertEqual(msgs[-3][1][0][0], DesMessageType.WARNING)
        self.assertIn("No tuple met the 'where' condition for updating", msgs[-3][1][0][1])
        self.assertIsNone(msgs[-3][1][0][2])
        # The second DML statement statement produces 1 DES message (warning)
        self.assertEqual(len(msgs[-2][1]), 1)
        self.assertEqual(msgs[-2][1][0][0], DesMessageType.WARNING)
        self.assertIn("No tuple met the 'where' condition for deleting", msgs[-2][1][0][1])
        self.assertIsNone(msgs[-2][1][0][2])
        # The third DML statement statement produces 1 DES message (error)
        self.assertEqual(len(msgs[-1][1]), 1)
        self.assertEqual(msgs[-1][1][0][0], DesMessageType.ERROR)
        self.assertIn("Primary key violation", msgs[-1][1][0][1])
        self.assertIsNone(msgs[-1][1][0][2])

    def test_dml_timeout(self):
        """ Timeout when checking a DML program with DES """
        insert = ''
        dml = f'INSERT INTO Persona ({self.__QUERY_TIMEOUT});'
        with self.assertRaises(DESException) as ctx:
            DesExecutor.get().get_des_messages_dml(self.__CREATE_TIMEOUT, insert, dml)
        self.assertIn("Timeout when invoking DES", str(ctx.exception))

    def test_des_dml_messages(self):
        """ Check that get_des_messages_solution() returns the correct messages """
        problem = DMLProblem(title_md='Test DML', text_md='bla bla bla',
                             create_sql="CREATE TABLE t(name VARCHAR(20) PRIMARY KEY, age INT)",
                             insert_sql="INSERT INTO t VALUES ('pepe', 3); INSERT INTO t VALUES ('ana', 13);",
                             solution="INSERT INTO t VALUES ('eva', 18)")

        code = ["INSERT INTO t VALUES ('eva', 18)",  # OK
                "UPDATE t SET age = 0 WHERE age = -9",  # No tuple met the condition
                "DELETE FROM t WHERE age = 10",  # No tuple met the condition
                "DELETE FROM t WHERE age = 13",  # OK, deletes 'ana'
                "UPDATE t SET age = 0 WHERE age > 3",  # OK, updates remaining row
                ]
        msgs = problem.get_des_messages_solution(";\n".join(code))
        self.assertEqual(len(msgs), 2)

        # Message for first UPDATE
        self.assertEqual(msgs[0][0], DesMessageType.WARNING)
        self.assertIn("No tuple met the 'where' condition for updating", msgs[0][1])
        self.assertEqual(code[1], msgs[0][2])  # The statement is the snippet

        # Message for first DELETE
        self.assertEqual(msgs[1][0], DesMessageType.WARNING)
        self.assertIn("No tuple met the 'where' condition for deleting", msgs[1][1])
        self.assertEqual(code[2], msgs[1][2])  # The statement is the snippet

    def test_messages_unsafe_dml(self):
        """ Test that messages are empty in unsafe submissions """
        create = "CREATE TABLE t(age INT);"
        insert = "INSERT INTO t VALUES (5);\nINSERT INTO t VALUES (55);"
        dml2 = "DELETE FROM t WHERE age = 83;"
        unsafe = "\\pwd"
        msgs = list(DesExecutor.get().get_des_messages_dml(create, insert, unsafe))
        self.assertEqual(len(msgs), 0)
        msgs = list(DesExecutor.get().get_des_messages_dml(create, unsafe, dml2))
        self.assertEqual(len(msgs), 0)
        msgs = list(DesExecutor.get().get_des_messages_dml(unsafe, insert, dml2))
        self.assertEqual(len(msgs), 0)

    def test_des_dml_timeout(self):
        """ When DES timeouts DMLProblem.get_des_messages_solution returns [] """
        problem = DMLProblem(title_md='Test DML', text_md='bla bla bla',
                             create_sql=self.__CREATE_TIMEOUT,
                             insert_sql='',
                             solution=f"INSERT INTO t ({self.__QUERY_TIMEOUT})")
        code = f"INSERT INTO t ({self.__QUERY_TIMEOUT})"
        msgs = problem.get_des_messages_solution(code)
        self.assertEqual(msgs, [])

    def test_validate_dml(self):
        """ Checks that validating a DMLProblem with errors returns some DES messages """
        problem = DMLProblem(title_md='Test DML', text_md='bla bla bla',
                             create_sql="CREATE TABLE t(name VARCHAR(20) PRIMARY KEY, age INT)",
                             insert_sql="INSERT INTO t VALUES ('pepe', 3); INSERT INTO t VALUES ('pepe', 13);",
                             solution="INSERT INTO t VALUES ('pepe', 18)")
        with self.assertRaises(ValidationError) as ctxt:
            problem.validate_des()
        exception = str(ctxt.exception)
        self.assertIn("Error code: 0", exception)
        self.assertIn("Primary key violation", exception)
        self.assertIn("t(pepe,13)", exception)

    def test_cannot_parse_des_output(self):
        """ Test that DES output that cannot be parsed generated an empty list of messages """
        output1 = """$success
1                                          
1                                          
1                                          
1                                          
Exception: Impossible type conversion: cast('Numero_de_Aficionados',number(float))

"""
        output2 = """$success
$success
$success
1                                          
1                                          
1                                          
1                                          
1                                          
1                                          
1                                          
1                                          
1                                          
1                                          
$error
0
Type mismatch Club.Nombre:string(varchar(40)) vs. string(varchar(20)).

"""
        with self.assertRaises(DESException):
            self.assertEqual(parse_tapi_commands(output1, 6, 0), [[]] * 6)
        with self.assertRaises(DESException):
            self.assertEqual(parse_tapi_commands(output2, 14, 0), [[]] * 14)

    def test_removing_unrecognized(self):
        """ Correctly removes <Unrecognized start of input> DES error messages """
        msgs = [
            [],
            [(DesMessageType.INFO, 'Gol de señor', None)],
            [(DesMessageType.ERROR, 'Unrecognized start of input.', None)],
            [(DesMessageType.ERROR, 'cosa very bad', None),
             (DesMessageType.ERROR, 'Unrecognized start of input.', None)],
            [(DesMessageType.ERROR, 'Unrecognized start of input.', None),
             (DesMessageType.ERROR, 'cosa very bad', None)],
            [(DesMessageType.INFO, 'Unrecognized start of input.', None)],  # Must be kept
            [(DesMessageType.ERROR, 'Something Unrecognized start of input in', None)],  # Must be kept
        ]
        expected_filtered_msgs = [
            [],
            [(DesMessageType.INFO, 'Gol de señor', None)],
            [],
            [(DesMessageType.ERROR, 'cosa very bad', None)],
            [(DesMessageType.ERROR, 'cosa very bad', None)],
            [(DesMessageType.INFO, 'Unrecognized start of input.', None)],
            [(DesMessageType.ERROR, 'Something Unrecognized start of input in', None)],
        ]
        filtered_msgs = filter_unrecognized_start_of_input(msgs, '', '', '')
        self.assertEqual(expected_filtered_msgs, filtered_msgs)

    def test_safe_des(self):
        """ Detects safe and safe SQL before executing DES """
        unsafe = ['\\version          ',
                  'SELECT * FROM Club; \\ls',
                  '\\version\nSELECT * FROM Club',
                  'INSERT INTO Club VALUES (1,2,3);\\version\nSELECT * FROM Club']
        safe = [
            "CREATE TABLE t(name VARCHAR(20) PRIMARY KEY, age INT); INSERT INTO t VALUES ('pepe', 3); INSERT INTO t VALUES ('ana', 13);",
            "CREATE TABLE t(name VARCHAR(20) PRIMARY KEY, age INT); INSERT INTO t VALUES ('pepe', 3); SELECT * FROM Club",
            "SELECT e.first_name, e.last_name FROM employees e WHERE e.salary > (SELECT AVG(inner_e.salary) FROM employees inner_e WHERE inner_e.department_id = e.department_id) AND e.department_id IN (SELECT d.department_id FROM departments d WHERE d.location = 'New York' AND (SELECT COUNT(*) FROM employees e2 WHERE e2.department_id = d.department_id) > 5);",
            """-- Create Tables
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    major VARCHAR(50)
);

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100),
    credits INT,
    department VARCHAR(50)
);

CREATE TABLE enrollments (
    student_id INT REFERENCES students(student_id),
    course_id INT REFERENCES courses(course_id),
    grade DECIMAL(3, 2)
);

-- Insert Values
INSERT INTO students (name, major) VALUES ('Alice', 'CS'), ('Bob', 'CS'), ('Charlie', 'Math'), ('David', 'CS');
INSERT INTO courses (course_name, credits, department) VALUES ('Database Systems', 4, 'CS'), ('Algorithms', 4, 'CS'), ('Calculus', 3, 'Math');
INSERT INTO enrollments VALUES (1, 1, 4.0), (1, 2, 3.5), (2, 1, 3.8), (3, 3, 3.9), (4, 1, 2.5);

SELECT s.name 
FROM students s 
WHERE (SELECT AVG(e.grade) 
       FROM enrollments e 
       WHERE e.student_id = s.student_id) > 
       (SELECT AVG(e2.grade) 
       FROM enrollments e2 JOIN courses c ON e2.course_id = c.course_id 
       WHERE c.department = 'CS') AND 
         (SELECT COUNT(*) FROM enrollments e3 WHERE e3.student_id = s.student_id) > 1;"""]
        for sql in unsafe:
            self.assertFalse(DesExecutor.is_safe_for_des(sql))
        for sql in safe:
            self.assertTrue(DesExecutor.is_safe_for_des(sql))
