"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Unit tests for the validation of statements using DES
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from judge.des_driver import parse_tapi_cmd, DesExecutor
from judge.types import DesMessageType
from judge.models import SelectProblem
from judge.exceptions import DESException


class DesTest(TestCase):
    """ Tests for des_driver """

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
        self.assertIn('Unable to parse DES output: <$erroro>', str(ctx.exception))


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
        msgs = list(DesExecutor.get().get_sql_messages_query(create, insert, query))
        self.assertEqual(len(msgs), 4)
        for _, msg in msgs:
            self.assertEqual(msg, [])

    def test_des_timeout(self):
        """ DES require too much time to process SQL query, so it is aborted and returns None """
        create = """
CREATE TABLE Club(
    CIF CHAR(9) PRIMARY KEY, 
    Nombre VARCHAR(40) NOT NULL UNIQUE, 
    Sede VARCHAR(30) NOT NULL, 
    Num_Socios INTEGER NOT NULL, 
    CONSTRAINT NumSociosPositivos CHECK(Num_Socios >= 0)
);

CREATE TABLE Patrocinador(
    CIF CHAR(9) PRIMARY KEY,
    NomPat VARCHAR(20) NOT NULL,
    Rama VARCHAR(20) NOT NULL,
    Eslogan VARCHAR(30) NOT NULL,
    CONSTRAINT NombreYRamaUnicos UNIQUE(NomPat, Rama)
);

CREATE TABLE Persona(
    NIF CHAR(9) PRIMARY KEY,
    Nombre VARCHAR(20) NOT NULL
);

CREATE TABLE Jugador(
    NIF CHAR(9) PRIMARY KEY REFERENCES Persona(NIF) ON DELETE CASCADE,
    Altura DECIMAL(3,2) NOT NULL CHECK (Altura > 0.0),
    CIF CHAR(9) NOT NULL REFERENCES Club(CIF)
);

CREATE TABLE Patrocina(
    NIF CHAR(9) NOT NULL REFERENCES Persona(NIF),
    CIF CHAR(9) NOT NULL REFERENCES Patrocinador(CIF),
    Cantidad DECIMAL(10,2) NOT NULL CHECK (Cantidad > 0.0),
    CONSTRAINT PKPatrocina PRIMARY KEY (NIF, CIF)
);
"""
        insert = ''
        query = '''
SELECT P.NIF, P.Nombre
FROM Jugador J JOIN Persona P ON J.NIF = P.NIF
WHERE NOT EXISTS ((SELECT CIF -- Todos los patrocinadores
                  FROM Patrocinador
                  WHERE Rama = 'Deportes')
                 MINUS
                 (SELECT CIF -- Todos los patrocinadores del jugador
                  FROM Patrocina P
                  WHER P.NIF = J.NIF));
'''
        msgs = DesExecutor.get().get_sql_messages_query(create, insert, query)
        self.assertIsNone(msgs)

    def test_validate_correct_problem(self):
        """ Test to validate with DES a correct SelectProblem """
        problem = SelectProblem(create_sql='CREATE TABLE t(age int)',
                          insert_sql='',
                          solution='SELECT * FROM t')
        self.assertIsNone(problem.validate_des())

    def test_validate_wrong_problem(self):
        """ Test to validate with DES a wrong SelectProblem """
        problem = SelectProblem(create_sql='CREATE TABLE t(age int)',
                          insert_sql='',
                          solution='SELECT * FROM table')
        problem2 = SelectProblem(create_sql='CREATE TABLE t(age int)',
                                 insert_sql='',
                                 solution='SELECT * FRO t')
        with self.assertRaises(ValidationError) as ctx:
            problem.validate_des()
        self.assertIn("Unknown table or view 'table'", ctx.exception.message)
        with self.assertRaises(ValidationError) as ctx:
            problem2.validate_des()
        self.assertIn("Expected FROM clause", ctx.exception.message)
