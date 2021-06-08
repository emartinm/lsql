# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the connection and execution of statements using the Oracle DB
"""
import os
import time

from django.test import TestCase

from judge.oracle_driver import OracleExecutor, clean_sql, line_col_from_offset
from judge.models import SelectProblem, Collection, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem, \
    DiscriminantProblem
from judge.types import VeredictCode, OracleStatusCode
from judge.exceptions import ExecutorException

SELECT_TLE = '''
        SELECT a, AVG(b), MAX(b), AVG(c), AVG(d)
        FROM (select 8 AS a, sqrt(8) as b from dual connect by level <= 5000)
             CROSS JOIN
             (select 8 as c, sqrt(8) as d from dual connect by level <= 5000)
        GROUP BY a;'''


class OracleTest(TestCase):
    """"Tests for oracle_driver"""

    def assert_executor_exception(self, function, status_code):
        """Checks if executing the nullary function raises an ExecutorException with the expected status_code"""
        with self.assertRaises(ExecutorException) as ctx:
            function()
        self.assertEqual(ctx.exception.error_code, status_code)

    def test_version(self):
        """Test for get_version()"""
        oracle = OracleExecutor.get()
        parts = oracle.get_version().split()
        self.assertEqual(parts[0], 'Oracle')
        self.assertTrue(int(parts[1].split('.')[0]) >= 11)

    def test_empty_clean_code(self):
        """Test for cleaning a null SQL code"""
        self.assertEqual(clean_sql(None), [])

    def test_clean_sql(self):
        """ Test for cleaning SQL code with several lines and interleaved comments """
        codes = [
            ("\n   \n  --hello\n   SELECT *\n\n  \n \n FROM Club     ;",
             ["\n   \n         \n   SELECT *\n\n  \n \n FROM Club      "]),
            ("\n--comment   \n  --hola\n   SELECT *\n\n  \n \n FROM Club     ;--mas",
             ["\n            \n        \n   SELECT *\n\n  \n \n FROM Club           "]),
            ('\n  --hello\n  \n  ---hi hi \nUPDATE Club\nSET Atletas = 2000;  --something\n   \n \n --hola   '
             '\nUPDATE Club\nSET Atletas = 107;',
             ['\n         \n  \n           \nUPDATE Club\nSET Atletas = 2000              \n   \n \n          '
              '\n           \n                  ',
              '\n         \n  \n           \n           \n                                \n   \n \n          '
              '\nUPDATE Club\nSET Atletas = 107 ']),
        ]
        for code, clean in codes:
            cleaned = clean_sql(code)
            self.assertEqual(cleaned, clean)
            for stmt in cleaned:
                # Every extended statement must have the same length as the original complete code
                self.assertEqual(len(code), len(stmt))

    def test_select(self):
        """Tests for SelectProblem.judge()"""
        collection = Collection()
        collection.save()
        create = '''CREATE TABLE "Nombre Club" (
                        CIF CHAR(9) PRIMARY KEY, -- No puede ser NULL
                        Nombre VARCHAR2(40) NOT NULL UNIQUE,
                        Sede VARCHAR2(30) NOT NULL,
                        Num_Socios NUMBER(10,0) NOT NULL,
                        CONSTRAINT NumSociosPositivos CHECK (Num_Socios >= 0)
                    );'''
        insert = '''INSERT INTO "Nombre Club" VALUES ('11111111X', 'Real Madrid CF', 'Concha Espina', 70000);
                    INSERT INTO "Nombre Club" VALUES ('11111112X', 'Futbol Club Barcelona', 'Aristides Maillol', 80000);
                    INSERT INTO "Nombre Club" VALUES ('11111113X', 'PSG', 'Rue du Commandant Guilbaud', 1000);'''
        solution = 'SELECT * FROM "Nombre Club";'
        oracle = OracleExecutor.get()
        problem = SelectProblem(title_md='Test Select', text_md='bla bla bla',
                                create_sql=create, insert_sql=insert, collection=collection,
                                author=None, check_order=False, solution=solution)
        problem.clean()  # Needed to compute extra HTML fields and solutions
        problem.save()

        # Time-limit
        tle = SELECT_TLE
        too_many_rows = f"select * from dual connect by level <= {int(os.environ['ORACLE_MAX_ROWS'])+1};"
        too_many_cols = f"select {','.join(['1']*(int(os.environ['ORACLE_MAX_COLS'])+1))} from dual;"
        self.assert_executor_exception(lambda: problem.judge(tle, oracle), OracleStatusCode.TLE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge(too_many_rows, oracle),
                                       OracleStatusCode.TLE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge(too_many_cols, oracle),
                                       OracleStatusCode.TLE_USER_CODE)

        # Validation error (only one statement supported)
        self.assert_executor_exception(lambda: problem.judge('', oracle), OracleStatusCode.NUMBER_STATEMENTS)
        self.assert_executor_exception(lambda: problem.judge('SELECT * FROM "Nombre Club"; SELECT * '
                                                                    'FROM "Nombre Club"',
                                                                    oracle), OracleStatusCode.NUMBER_STATEMENTS)

        # Runtime error
        self.assert_executor_exception(lambda: problem.judge('SELECT * from "Nombre ClubE"', oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge('SELECT * from Club', oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge('SELECT * FROM', oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)

        # Correct solution
        self.assertEqual(problem.judge(solution, oracle)[0], VeredictCode.AC)
        self.assertEqual(problem.judge('SELECT CIF, NOmbre, Sede, Num_Socios FROM "Nombre Club"', oracle)[0],
                         VeredictCode.AC)
        self.assertEqual(problem.judge('SELECT * FROM "Nombre Club" ORDER BY Num_Socios ASC', oracle)[0],
                         VeredictCode.AC)

        # Incorrect solution
        self.assertEqual(problem.judge('SELECT CIF FROM "Nombre Club"', oracle)[0], VeredictCode.WA)
        self.assertEqual(problem.judge('SELECT * FROM "Nombre Club" WHERE Num_Socios < 50000', oracle)[0],
                         VeredictCode.WA)

    def test_dml(self):
        """Tests for DMLProblem.judge()"""
        collection = Collection()
        collection.save()
        create = '''CREATE TABLE Club(
                        CIF CHAR(9) PRIMARY KEY, -- No puede ser NULL
                        Nombre VARCHAR2(40) NOT NULL UNIQUE,
                        Sede VARCHAR2(30) NOT NULL,
                        Num_Socios NUMBER(10,0) NOT NULL,
                        CONSTRAINT NumSociosPositivos CHECK (Num_Socios >= 0)
                    );'''
        insert = '''INSERT INTO Club VALUES ('11111111X', 'Real Madrid CF', 'Concha Espina', 70000);
                    INSERT INTO Club VALUES ('11111112X', 'Futbol Club Barcelona', 'Aristides Maillol', 80000);
                    INSERT INTO Club VALUES ('11111113X', 'PSG', 'Rue du Commandant Guilbaud', 1000);'''
        solution = """INSERT INTO Club VALUES ('11111114X', 'Real Betis Balompié', 'Av. de Heliópolis, s/n', 45000);
                      INSERT INTO Club VALUES ('11111115X', 'Un otro equipo', 'Calle falsa, 123', 25478);"""
        incorrect1 = """INSERT INTO Club VALUES ('11111114X', 'Real Betis Balompié', 'Av. de Heliópolis, s/n', 45001);
                        INSERT INTO Club VALUES ('11111115X', 'Un otro equipo', 'Calle falsa, 123', 25478);"""
        incorrect2 = """INSERT INTO Club VALUES ('11111114X', 'Real Betis Balompié', 'Av. de Heliópolis, s/n', 45000);
                        INSERT INTO Club VALUES ('11111115Z', 'Un otro equipo', 'Calle falsa, 123', 25478);"""
        syntax_err = """INSERT INTO Club VALUES ('11111114X', 'Real Betis Balompié', 'Av. de Heliópolis, s/n', 45000);
                        INSERT INTO Club VALUE ('11111115X', 'Un otro equipo', 'Calle falsa, 123', 25478);"""
        solution_order = """
          INSERT INTO Club VALUES ('11111115X', 'Un otro equipo', 'Calle falsa, 123', 25478);
          INSERT INTO Club VALUES ('11111114X', 'Real Betis Balompié', 'Av. de Heliópolis, s/n', 45000);
        """
        # Time-limit
        tle = '''
            INSERT INTO Club
                SELECT CIF, MIN(Nombre) AS nombre, MAX(Sede) as sede, AVG(Num_socios) as Num_socios
                FROM (select '00000000X' AS CIF, 'a' as Nombre from dual connect by level <= 5000)
                     CROSS JOIN
                     (select 'b' as Sede, 56789 AS Num_Socios from dual connect by level <= 5000)
                GROUP BY CIF;'''
        # Creates a table with ORACLE_MAX_ROWS + 1 rows
        too_many_rows = f"""
            INSERT INTO Club
            SELECT level || '3333X', level || 'a', 'b', 45 from dual 
            connect by level <= {int(os.environ['ORACLE_MAX_ROWS'])+1};
            """
        # Create a table with ORACLE_MAX_COLS + 1 columns
        too_many_cols = "CREATE TABLE Test( "
        for i in range(int(os.environ['ORACLE_MAX_COLS'])):
            too_many_cols += f"col{i} NUMBER, "
        too_many_cols += "col_end NUMBER);"

        # Creates ORACLE_MAX_TABLES + 1 tables
        too_many_tables = ""
        for i in range(int(os.environ['ORACLE_MAX_TABLES'])+1):
            too_many_tables += f"CREATE TABLE table{i}(n NUMBER);"

        oracle = OracleExecutor.get()
        problem = DMLProblem(title_md='Test DML', text_md='bla bla bla',
                             create_sql=create, insert_sql=insert, collection=collection,
                             min_stmt=2, max_stmt=2,
                             author=None, check_order=False, solution=solution)
        problem2 = DMLProblem(title_md='DML problem', text_md='bla bla bla',
                              create_sql=create, insert_sql=insert, collection=collection,
                              min_stmt=0, max_stmt=100,
                              author=None, check_order=False, solution=solution)
        problem.clean()  # Needed to compute extra fields and solutions
        problem.save()
        problem2.clean()
        problem.save()

        # Validation error (there should be exactly 2 statements)
        self.assert_executor_exception(
            lambda: problem.judge("INSERT INTO Club VALUES ('11111114X', 'R', 'A', 45000)", oracle),
            OracleStatusCode.NUMBER_STATEMENTS)
        self.assert_executor_exception(
            lambda: problem.judge("""INSERT INTO Club VALUES ('11111114X', 'R', 'A', 45000);
                                     INSERT INTO Club VALUES ('11111114X', 'R', 'A', 45000);
                                     INSERT INTO Club VALUES ('11111114X', 'R', 'A', 45000)""", oracle),
            OracleStatusCode.NUMBER_STATEMENTS)

        # Runtime error
        self.assert_executor_exception(
            lambda: problem.judge("""INSERT Club VALUES ('11111114X', 'R', 'A', 45000);
                                     INSERT INTO Club VALUES ('11111114X', 'R', 'A', 45000);""", oracle),
            OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(
            lambda: problem.judge("""INSERT INTO Club VALUES ('11111114X', 'R', 'A', 45000);
                                     INSERT Club VALUES ('11111114X', 'R', 'A', 45000);""", oracle),
            OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(
            lambda: problem.judge(syntax_err, oracle), OracleStatusCode.EXECUTE_USER_CODE)

        # Correct solution
        self.assertEqual(problem.judge(solution, oracle)[0], VeredictCode.AC)
        self.assertEqual(problem.judge(solution_order, oracle)[0], VeredictCode.AC)

        # Incorrect solution
        self.assertEqual(problem.judge(incorrect1, oracle)[0], VeredictCode.WA)
        self.assertEqual(problem.judge(incorrect2, oracle)[0], VeredictCode.WA)

        # Time-limit
        self.assert_executor_exception(lambda: problem2.judge(tle, oracle), OracleStatusCode.TLE_USER_CODE)
        self.assert_executor_exception(lambda: problem2.judge(too_many_rows, oracle), OracleStatusCode.TLE_USER_CODE)
        self.assert_executor_exception(lambda: problem2.judge(too_many_cols, oracle), OracleStatusCode.TLE_USER_CODE)

        # Too many tables
        self.assert_executor_exception(lambda: problem2.judge(too_many_tables, oracle), OracleStatusCode.TLE_USER_CODE)

    def test_function(self):
        """Tests for FunctionProblem.judge()"""
        collection = Collection()
        collection.save()
        create = ''
        insert = ''
        solution = """
            CREATE OR REPLACE FUNCTION golesLocal(resultado VARCHAR2) RETURN NUMBER IS
                posGuion NUMBER;
                golesStr VARCHAR2(3);
            BEGIN
                posGuion := INSTR(resultado, '-');
                golesStr := SUBSTR(resultado, 0, posGuion - 1);
                RETURN TO_NUMBER(golesStr); 
            END;"""
        calls = """
                golesLocal('2-1')
                golesLocal('0-1')
                golesLocal('12-13')
                golesLocal('117-99')
                """

        # Funcion definition is syntactically incorrect
        compile_error = """
            CREATE OR REPLACE FUNCTION golesLocal(resultado VARCHAR2) RETURN NUMBER IS
                posGuion NUMBER;
                golesStr VARCHAR2(3);
            BEGIN
                posGuion := INSTR(resultado, '-');
                golesStr := SUBSTR(resultado, 0, posGuion - 1; -- missing bracket
                RETURN TO_NUMBER(golesStr); 
            END;"""
        # The execution produces a division by zero
        runtime_error1 = """
            CREATE OR REPLACE FUNCTION golesLocal(resultado VARCHAR2) RETURN NUMBER IS
                posGuion NUMBER;
                golesStr VARCHAR2(3);
            BEGIN
                RETURN 1 / 0; 
            END;"""
        # The function parameter (NUMBER) does not match the actual value (VARCHAR)
        runtime_error2 = """
            CREATE OR REPLACE FUNCTION golesLocal(resultado NUMBER) RETURN NUMBER IS
            BEGIN
                RETURN resultado; 
            END;"""
        # Retuns 2x the expected value
        wrong_answer = """
            CREATE OR REPLACE FUNCTION golesLocal(resultado VARCHAR2) RETURN NUMBER IS
                posGuion NUMBER;
                golesStr VARCHAR2(3);
            BEGIN
                posGuion := INSTR(resultado, '-');
                golesStr := SUBSTR(resultado, 0, posGuion - 1);
                RETURN TO_NUMBER(golesStr) * 2; -- Doubled 
            END;"""
        # Waits for 11 seconds
        tle = """
                CREATE OR REPLACE FUNCTION golesLocal(resultado VARCHAR2) RETURN NUMBER IS
                    IN_TIME INT := 11; --num seconds
                    v_now DATE;
                BEGIN
                    SELECT SYSDATE INTO v_now FROM DUAL;
                    LOOP
                        EXIT WHEN v_now + (IN_TIME * (1/86400)) <= SYSDATE;
                    END LOOP;  
                    RETURN 54;
                END;"""
        bad_name = """
                    CREATE OR REPLACE FUNCTION golesLocalES(resultado VARCHAR2) RETURN NUMBER IS
                        posGuion NUMBER;
                        golesStr VARCHAR2(3);
                    BEGIN
                        posGuion := INSTR(resultado, '-');
                        golesStr := SUBSTR(resultado, 0, posGuion - 1);
                        RETURN TO_NUMBER(golesStr); 
                    END;"""
        oracle = OracleExecutor.get()
        problem = FunctionProblem(title_md='Test Function', text_md='bla bla bla',
                                  create_sql=create, insert_sql=insert, collection=collection,
                                  author=None, solution=solution, calls=calls)
        problem.clean()  # Needed to compute extra HTML fields and solutions
        problem.save()

        # Time-limit
        self.assert_executor_exception(lambda: problem.judge(tle, oracle), OracleStatusCode.TLE_USER_CODE)

        # Error when compiling user function
        self.assert_executor_exception(lambda: problem.judge(compile_error, oracle), OracleStatusCode.COMPILATION_ERROR)

        # Error when invoking user function
        self.assert_executor_exception(lambda: problem.judge(runtime_error1, oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge(runtime_error2, oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge(bad_name, oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)

        # Correct solution
        self.assertEqual(problem.judge(solution, oracle)[0], VeredictCode.AC)

        # Incorrect solution
        self.assertEqual(problem.judge(wrong_answer, oracle)[0], VeredictCode.WA)

    def test_proc(self):
        """Tests for ProcProblem.judge()"""
        collection = Collection()
        collection.save()
        create = '''CREATE TABLE Club(
                        CIF CHAR(9) PRIMARY KEY, -- No puede ser NULL
                        Nombre VARCHAR2(40) NOT NULL UNIQUE,
                        Sede VARCHAR2(30) NOT NULL,
                        Num_Socios NUMBER(10,0) NOT NULL,
                        CONSTRAINT NumSociosPositivos CHECK (Num_Socios >= 0)
                    );'''
        insert = """INSERT INTO Club VALUES ('11111111X', 'Real Madrid CF', 'Concha Espina', 70000);
                    INSERT INTO Club VALUES ('11111112X', 'Futbol Club Barcelona', 'Aristides Maillol', 80000);
                    INSERT INTO Club VALUES ('11111113X', 'PSG', 'Rue du Commandant Guilbaud', 1000);"""
        solution = """
            CREATE OR REPLACE PROCEDURE inserta(x NUMBER) IS
                num_equipos NUMBER;
            BEGIN
                SELECT COUNT(*) INTO num_equipos FROM Club;
                INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos + x);
            END;"""
        call = "inserta(4)"

        # Time-limit
        tle = """
                CREATE OR REPLACE PROCEDURE inserta(x NUMBER) IS
                    num_equipos NUMBER;
                    IN_TIME INT := 11; --num seconds
                    v_now DATE;
                BEGIN
                    SELECT SYSDATE INTO v_now FROM DUAL;
                    SELECT COUNT(*) INTO num_equipos FROM Club;
                    LOOP
                        EXIT WHEN v_now + (IN_TIME * (1/86400)) <= SYSDATE;
                    END LOOP;  
                    INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos + x);
                END;"""
        # Error in the procedure code
        compile_error = """
                CREATE OR REPLACE PROCEDURE inserta(x NUMBER) IS
                    num_equipos NUMBER;
                BEGIN
                    SELECT SYSDATE INTO v_now DUAL; -- Falta FROM
                    INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos + x);
                END;"""
        # Division by zero
        runtime_error1 = """
                CREATE OR REPLACE PROCEDURE inserta(x NUMBER) IS
                    num_equipos NUMBER;
                BEGIN
                    SELECT COUNT(*) INTO num_equipos FROM Club;
                    INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos / 0); -- Division by zero
                END;"""
        # Incompatible type in parameter
        runtime_error2 = """
                CREATE OR REPLACE PROCEDURE inserta(x DATE) IS -- Incorrect parameter when invoked
                    num_equipos NUMBER;
                BEGIN
                    SELECT COUNT(*) INTO num_equipos FROM Club;
                    INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos);
                END;"""
        wrong_answer = """
            CREATE OR REPLACE PROCEDURE inserta(x NUMBER) IS
                num_equipos NUMBER;
            BEGIN
                SELECT COUNT(*) INTO num_equipos FROM Club;
                INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos + x + 2);
            END;"""
        bad_name = """
                    CREATE OR REPLACE PROCEDURE insertaR(x NUMBER) IS
                        num_equipos NUMBER;
                    BEGIN
                        SELECT COUNT(*) INTO num_equipos FROM Club;
                        INSERT INTO CLUB VALUES ('22222222X', 'A', 'B', num_equipos + x);
                    END;"""

        oracle = OracleExecutor.get()
        problem = ProcProblem(title_md='Test Function', text_md='bla bla bla',
                              create_sql=create, insert_sql=insert, collection=collection,
                              author=None, solution=solution, proc_call=call)
        problem.clean()  # Needed to compute extra HTML fields and solutions
        problem.save()

        # Time-limit
        self.assert_executor_exception(lambda: problem.judge(tle, oracle), OracleStatusCode.TLE_USER_CODE)

        # Error when compiling user function
        self.assert_executor_exception(lambda: problem.judge(compile_error, oracle), OracleStatusCode.COMPILATION_ERROR)

        # Error when invoking user function
        self.assert_executor_exception(lambda: problem.judge(runtime_error1, oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge(runtime_error2, oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)
        self.assert_executor_exception(lambda: problem.judge(bad_name, oracle),
                                       OracleStatusCode.EXECUTE_USER_CODE)

        # Correct solution
        self.assertEqual(problem.judge(solution, oracle)[0], VeredictCode.AC)

        # Incorrect solution
        self.assertEqual(problem.judge(wrong_answer, oracle)[0], VeredictCode.WA)

    def test_trigger(self):
        """Tests for TriggerProblem.judge()"""
        collection = Collection()
        collection.save()
        create = '''CREATE TABLE Club(
                        CIF CHAR(9) PRIMARY KEY, -- No puede ser NULL
                        Nombre VARCHAR2(40) NOT NULL UNIQUE,
                        Sede VARCHAR2(30) NOT NULL,
                        Num_Socios NUMBER(10,0) NOT NULL,
                        CONSTRAINT NumSociosPositivos CHECK (Num_Socios >= 0)
                    );'''
        insert = """INSERT INTO Club VALUES ('11111111X', 'Real Madrid CF', 'Concha Espina', 70000);
                    INSERT INTO Club VALUES ('11111112X', 'Futbol Club Barcelona', 'Aristides Maillol', 80000);
                    INSERT INTO Club VALUES ('11111113X', 'PSG', 'Rue du Commandant Guilbaud', 1000);"""
        solution = """
            CREATE OR REPLACE TRIGGER IncrementaNumSocios
            BEFORE INSERT OR UPDATE
            ON Club FOR EACH ROW
            DECLARE
                numClubes NUMBER;
            BEGIN
                SELECT 4000 INTO numClubes FROM DUAL;
                :NEW.Num_Socios := :NEW.Num_Socios + numClubes * 100;
            END;"""
        tests = """
            INSERT INTO Club VALUES ('22222222X', 'FALSO', 'Calle', 30000);
            UPDATE Club SET Num_Socios = 70000 WHERE CIF = '11111113X';"""

        # Time-limit
        tle = """
            CREATE OR REPLACE TRIGGER IncrementaNumSocios
            BEFORE INSERT OR UPDATE
            ON Club FOR EACH ROW
            DECLARE
                numClubes NUMBER;
                IN_TIME INT := 11; --num seconds
                v_now DATE;
            BEGIN
                LOOP
                    EXIT WHEN v_now + (IN_TIME * (1/86400)) <= SYSDATE;
                END LOOP;  
                SELECT 4000 INTO numClubes FROM DUAL;
                :NEW.Num_Socios := :NEW.Num_Socios + numClubes * 100;
            END;"""
        # Error in the trigger code
        compile_error = """
            CREATE OR REPLACE TRIGGER IncrementaNumSocios
            BEFORE INSERT OR UPDATE
            ON Club FOR EACH ROW
            DECLARE
                numClubes NUMBER;
            BEGIN
                SELECT 4000 INTO numClubes FROM DUAL;
                :NEW.Num_Socios := :NEW.Num_Socios + numClubes 100; -- missing operator
            END;"""
        # Division by zero
        runtime_error = """
            CREATE OR REPLACE TRIGGER IncrementaNumSocios
            BEFORE INSERT OR UPDATE
            ON Club FOR EACH ROW
            DECLARE
                numClubes NUMBER;
            BEGIN
                SELECT 4000 INTO numClubes FROM DUAL;
                :NEW.Num_Socios := :NEW.Num_Socios + numClubes / 0;
            END;"""
        wrong_answer = """
            CREATE OR REPLACE TRIGGER IncrementaNumSocios
            BEFORE INSERT OR UPDATE
            ON Club FOR EACH ROW
            DECLARE
                numClubes NUMBER;
            BEGIN
                SELECT 4000 INTO numClubes FROM DUAL;
                :NEW.Num_Socios := :NEW.Num_Socios + numClubes * 10000;
            END;"""

        oracle = OracleExecutor.get()
        problem = TriggerProblem(title_md='Test Function', text_md='bla bla bla',
                                 create_sql=create, insert_sql=insert, collection=collection,
                                 author=None, solution=solution, tests=tests)
        problem.clean()  # Needed to compute extra HTML fields and solutions
        problem.save()

        # Time-limit
        self.assert_executor_exception(lambda: problem.judge(tle, oracle), OracleStatusCode.TLE_USER_CODE)

        # Error when compiling user function
        self.assert_executor_exception(lambda: problem.judge(compile_error, oracle), OracleStatusCode.COMPILATION_ERROR)

        # Error when invoking user function
        self.assert_executor_exception(lambda: problem.judge(runtime_error, oracle), OracleStatusCode.EXECUTE_USER_CODE)

        # Correct solution
        self.assertEqual(problem.judge(solution, oracle)[0], VeredictCode.AC)

        # Incorrect solution
        self.assertEqual(problem.judge(wrong_answer, oracle)[0], VeredictCode.WA)

    def test_discriminant(self):
        """Tests for DiscriminantProblem.judge(): clubs with more than 1000 followers"""
        collection = Collection()
        collection.save()
        create = '''CREATE TABLE Club(
                      CIF CHAR(9) PRIMARY KEY, -- No puede ser NULL
                      Nombre VARCHAR2(40) NOT NULL UNIQUE,
                      Sede VARCHAR2(30) NOT NULL,
                      Num_Socios NUMBER(10,0) NOT NULL,
                      CONSTRAINT NumSociosPositivos CHECK (Num_Socios >= 0)
                    );'''
        insert = """INSERT INTO Club VALUES ('11111111X', 'RMCF', 'Concha Espina', 70000);
                    INSERT INTO Club VALUES ('11111112X', 'FCB', 'Aristides Maillol', 80000);
                    INSERT INTO Club VALUES ('11111113X', 'PSG', 'Rue du Commandant Guilbaud', 1000);"""
        correct_query = "SELECT * FROM Club WHERE Num_Socios >= 1000;"
        incorrect_query = "SELECT * FROM Club;"

        # User solutions
        accepted = "INSERT INTO Club VALUES ('11111114X', 'XXX', 'YYY', 300)"
        wrong_answer = "INSERT INTO Club VALUES ('11111114X', 'XXX', 'YYY', 3000)"
        runtime_error = ["INSERT INTO Club VALUES ('11111114X', 'XXX', 'YYY', 'AAA')",
                         "INSERT INTO Club VALUES ('11111114X', 'XXX', 'YYY')",
                         "INSERT INTO Club VALUES ()",
                         "INSERT INT Club VALUES ('11111114X', 'XXX', 'YYY', 3000)",
                         "INSER INTO Club VALUES ('11111114X', 'XXX', 'YYY', 3000)"
                         ]

        tle = '''
            INSERT INTO Club
                SELECT CIF, MIN(Nombre) AS nombre, MAX(Sede) as sede, AVG(Num_socios) as Num_socios
                FROM (select '00000000X' AS CIF, 'a' as Nombre from dual connect by level <= 5000)
                     CROSS JOIN
                     (select 'b' as Sede, 56789 AS Num_Socios from dual connect by level <= 5000)
                GROUP BY CIF;'''

        oracle = OracleExecutor.get()
        problem = DiscriminantProblem(title_md='Test Discriminant', text_md='bla bla bla', create_sql=create,
                                      insert_sql=insert, collection=collection, author=None,
                                      incorrect_query=incorrect_query, correct_query=correct_query)
        problem.clean()  # Needed to compute extra HTML fields and solutions
        problem.save()

        # Time-limit
        self.assert_executor_exception(lambda: problem.judge(tle, oracle), OracleStatusCode.TLE_USER_CODE)

        # Error when inserting syntactically invalid user rows
        for code in runtime_error:
            with self.assertRaises(ExecutorException) as ctx:
                problem.judge(code, oracle)
            self.assertEqual(ctx.exception.error_code, OracleStatusCode.EXECUTE_USER_CODE)

        # Correct solution
        self.assertEqual(problem.judge(accepted, oracle)[0], VeredictCode.AC)

        # Incorrect solution
        self.assertEqual(problem.judge(wrong_answer, oracle)[0], VeredictCode.WA)

    def test_table_with_date(self):
        """Check that DATEs are correctly stored and retrived from the DB, and comparing them to a new obtained
        value works as expected"""
        collection = Collection()
        collection.save()
        create = 'CREATE TABLE test (day DATE);'
        insert = "INSERT INTO test VALUES (TO_DATE('2003/07/09', 'yyyy/mm/dd'))"
        solution = 'SELECT * FROM test'
        select_problem = SelectProblem(title_md='Dates', text_md='Example with dates',
                                create_sql=create, insert_sql=insert, collection=collection,
                                solution=solution)
        select_problem.clean()
        select_problem.save()
        oracle = OracleExecutor.get()
        veredict, _ = select_problem.judge(solution, oracle)
        self.assertEqual(veredict, VeredictCode.AC)
        veredict, _ = select_problem.judge("SELECT TO_DATE('2003/07/09', 'yyyy/mm/dd') AS day FROM dual", oracle)
        self.assertEqual(veredict, VeredictCode.AC)

    def test_dangling_users(self):
        """Removes a manually created dangling user with an open connection"""
        oracle = OracleExecutor.get()
        gestor = oracle.connection_pool.acquire()
        user, passwd = oracle.create_user(gestor)
        oracle.create_connection(user, passwd)
        oracle.connection_pool.release(gestor)
        time.sleep(2)

        before = oracle.get_number_dangling_users(age_seconds=1)
        self.assertGreater(before, 0)  # There is a user created more than 1 second ago
        oracle.remove_dangling_users(age_seconds=1)
        after = oracle.get_number_dangling_users(age_seconds=1)
        self.assertGreater(before, after)  # There are less dangling users (we cannot assure all have dissapear )

    def test_pos_from_offset(self):
        """Test the extraction of line-col from offset"""
        code = """SELECT cif, sede
FROM club
WHERE num_socios > 0
      AND num_socios < 10;"""
        self.assertEqual(line_col_from_offset(code, 0), (0, 0))
        self.assertEqual(line_col_from_offset(code, 12), (0, 12))
        self.assertEqual(line_col_from_offset(code, 16), (0, 16))
        self.assertEqual(line_col_from_offset(code, 22), (1, 5))
        self.assertEqual(line_col_from_offset(code, 27), (2, 0))
        self.assertEqual(line_col_from_offset(code, 33), (2, 6))
        self.assertEqual(line_col_from_offset(code, 71), (3, 23))
