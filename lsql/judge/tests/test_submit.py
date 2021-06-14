# -*- coding: utf-8 -*-
"""
Unit tests for the submits
"""
import os

from django.test import TestCase, Client
from django.urls import reverse

from judge.tests.test_parse import ParseTest
from judge.models import FunctionProblem, ProcProblem, TriggerProblem, DiscriminantProblem, \
    NumSubmissionsProblemsAchievementDefinition, ObtainedAchievement, NumSolvedTypeAchievementDefinition, \
    SelectProblem
from judge.tests.test_views import create_collection, create_user, create_select_problem, create_dml_problem
from judge.types import VeredictCode, ProblemType


def create_discriminant_problem(important_order, collection, name='Ejemplo'):
    """Creates and stores a Discriminant DB Problem"""
    if not important_order:
        create = 'CREATE TABLE test_table_1 (n NUMBER);'
        insert = "INSERT INTO test_table_1 VALUES (1997);"
        incorrect = 'SELECT * FROM test_table_1;'
        correct = 'SELECT * FROM test_table_1 WHERE n > 1000;'
    else:
        create = 'CREATE TABLE test_table_1 (x NUMBER, n NUMBER);'
        insert = "INSERT INTO test_table_1 VALUES (1997, 1997);\
                  INSERT INTO test_table_1  VALUES (1994, 1994);"
        correct = 'SELECT * FROM test_table_1 ORDER BY n ASC'
        incorrect = 'SELECT * FROM test_table_1 ORDER BY x ASC'
    problem = DiscriminantProblem(title_md=name, text_md='texto largo', create_sql=create, insert_sql=insert,
                                  correct_query=correct, incorrect_query=incorrect, check_order=important_order,
                                  collection=collection)
    problem.clean()
    problem.save()
    return problem


class SubmitTest(TestCase):
    """Tests for Submits"""

    def test_compile_error(self):
        """Submitting code for a function/procedure/trigger with a compile error does resturn a
        OracleStatusCode.COMPILATION_ERROR"""
        curr_path = os.path.dirname(__file__)
        zip_function_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.TRIGGER_OK)

        client = Client()
        collection = create_collection('Colleccion de prueba AAA')
        user = create_user('54522', 'antonio')
        client.login(username='antonio', password='54522')

        function_problem = FunctionProblem(zipfile=zip_function_path, collection=collection, author=user)
        proc_problem = ProcProblem(zipfile=zip_proc_path, collection=collection, author=user)
        trigger_problem = TriggerProblem(zipfile=zip_trigger_path, collection=collection, author=user)

        funct_compile_error = """
                            CREATE OR REPLACE FUNCTION golesLocal(resultado VARCHAR2) RETURN NUMBER IS
                              posGuion NUMBER;
                              golesStr VARCHAR2(3);
                            BEGIN
                              posGuion := INSTR(resultado, '-') -- Missing ';'
                              golesStr := SUBSTR(resultado, 0, posGuion - 1);
                              RETURN TO_NUMBER(golesStr); 
                            END;"""
        proc_compile_error = """
            CREATE OR REPLACE PROCEDURE actualiza_socios(club_cif CHAR) IS
                CURSOR cr_partidos IS SELECT CL.Nombre AS ClubL, CV.Nombre AS ClubV, COUNT(*) AS NAsistentes
                                      FROM Enfrenta JOIN Asiste USING(CIF_local, CIF_visitante)
                                           JOIN Club CL ON CL.CIF = CIF_Local
                                           JOIN Club CV ON CV.CIF = CIF_visitante
                                      WHERE CIF_local = club_cif OR CIF_visitante = club_cif
                                      GROUP BY CIF_local, CIF_visitante, CL.Nombre, CV.Nombre;
                incrPartido NUMBER;
                incrTotal NUMBER := 0;
                nPartido NUMBER := 1;
                nombreClub VARCHAR2(200);
            BEGIN
                SELECT Nombre 
                INTO nombreClub
                FROM Club
                WHERE CIF = club_cif;

                FOR partido IN cr_partidos LOOP
                  IF partido.NAsistentes > 3 THEN
                    incrPartido := 100;
                  ELSIF partido.NAsistentes > 1 -- Missing 'THEN'
                    incrPartido := 10;
                  ELSE 
                    incrPartido := 0;
                  END IF;
                  incrTotal := incrTotal + incrPartido;
                  nPartido := nPartido + 1;
                END LOOP;

                UPDATE Club
                SET Num_Socios = Num_Socios + incrTotal
                WHERE CIF = club_cif;
            END;"""

        trigger_compile_error = """
                                CREATE OR REPLACE TRIGGER DispCantidadFinanciacion
                                BEFORE INSERT OR UPDATE
                                ON Financia FOR EACH ROW
                                DECLARE
                                  numJug NUMBER;
                                BEGIN
                                  SELECT COUNT(*) INTO numJug
                                  FROM Jugador
                                  WHERE CIF = :NEW.CIF_C;

                                  IF numJug >= 2 THEN
                                    :NEW.Cantidad := :NEW.Cantidad  1.25; -- Missing operator
                                  END IF;
                                END;"""

        for (problem, code) in [(function_problem, funct_compile_error),
                                (proc_problem, proc_compile_error),
                                (trigger_problem, trigger_compile_error)]:
            problem.clean()
            problem.save()
            submit_url = reverse('judge:submit', args=[problem.pk])
            response = client.post(submit_url, {'code': code}, follow=True)
            self.assertEqual(response.json()['veredict'], VeredictCode.WA)
            self.assertIn('error', response.json()['feedback'])
            self.assertIn('compil', response.json()['feedback'])

    def test_plsql_correct(self):
        """Accepted submissions to function/procedure/trigger problem"""

        curr_path = os.path.dirname(__file__)
        zip_function_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.TRIGGER_OK)

        client = Client()
        collection = create_collection('Colleccion de prueba AAA')
        user = create_user('54522', 'antonio')
        client.login(username='antonio', password='54522')

        function_problem = FunctionProblem(zipfile=zip_function_path, collection=collection, author=user)
        proc_problem = ProcProblem(zipfile=zip_proc_path, collection=collection, author=user)
        trigger_problem = TriggerProblem(zipfile=zip_trigger_path, collection=collection, author=user)

        for problem in [function_problem, proc_problem, trigger_problem]:
            problem.clean()
            problem.save()
            submit_url = reverse('judge:submit', args=[problem.pk])
            response = client.post(submit_url, {'code': problem.solution}, follow=True)
            self.assertEqual(response.json()['veredict'], VeredictCode.AC)

    def test_validation_error(self):
        """Test messages obtained in submission that do not containt the correct number of statements"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        dml_problem = create_dml_problem(collection, 'DML Problem')
        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')

        submit_url_select = reverse('judge:submit', args=[select_problem.pk])
        submit_url_dml = reverse('judge:submit', args=[dml_problem.pk])

        # JSON with VE and correct message for one SQL
        response = client.post(submit_url_select, {'code': f'{select_problem.solution}; {select_problem.solution}'},
                               follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.VE)
        self.assertIn('exactamente 1 sentencia SQL', response.json()['message'])

        # JSON with VE and correct message for 1--3 SQL
        stmt = 'INSERT INTO test VALUES (25);'
        response = client.post(submit_url_dml, {'code': stmt}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.VE)
        self.assertIn('entre 2 y 3 sentencias SQL', response.json()['message'])

        stmt = 'INSERT INTO test VALUES (25); INSERT INTO test VALUES (50); INSERT INTO test VALUES (75);' \
               'INSERT INTO test VALUES (100);'
        response = client.post(submit_url_dml, {'code': stmt}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.VE)
        self.assertIn('entre 2 y 3 sentencias SQL', response.json()['message'])

        # JSON with VE and correct message for less than 10 characters
        stmt = 'holis'
        response = client.post(submit_url_dml, {'code': stmt}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.VE)
        self.assertIn('tu solución no está vacía', response.json()['message'])

    def test_select_no_output(self):
        """Test that SQL statements that produce no results generate WA in a SELECT problem because
        the schema is different"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')
        stmts = ["CREATE VIEW my_test(n) AS SELECT n FROM test;",
                 "INSERT INTO test VALUES (89547);",
                 ]
        submit_url_select = reverse('judge:submit', args=[select_problem.pk])

        for stmt in stmts:
            response = client.post(submit_url_select, {'code': stmt}, follow=True)
            self.assertEqual(response.json()['veredict'], VeredictCode.WA)
            self.assertIn('Generado por tu código SQL: 0 columnas', response.json()['feedback'])

    def test_discriminant_problem(self):
        """Test for the view of a discriminant problem"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        create_user('contra', 'moragues')
        client.login(username='moragues', password='contra')
        disc_problem = create_discriminant_problem(False, collection)
        submit_discriminant_url = reverse('judge:submit', args=[disc_problem.pk])

        # Checks that invalid INSERTs are mappet to RE
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table_1 VALUES (a);'}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.RE)
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table_1 VALUES ()'}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.RE)
        response = client.post(submit_discriminant_url, {'code': 'INSERT merienda;'}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.RE)

        # Check a correct answer and an incorrect
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table_1 VALUES (500)'}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.AC)
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table_1 VALUES (2021)'}, follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.WA)

        problem_url = reverse('judge:problem', args=[disc_problem.pk])
        response = client.get(problem_url, follow=True)
        self.assertIn('Consulta SQL errónea a depurar', response.content.decode('utf-8'))
        disc_problem = create_discriminant_problem(True, collection)
        submit_discriminant_url = reverse('judge:submit', args=[disc_problem.pk])
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table_1 VALUES (2000, 1990)'},
                               follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.AC)
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table_1 VALUES (2000, 2000)'},
                               follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.WA)
        response = client.post(submit_discriminant_url, {'code': 'INSERT INTO test_table VALUES (2000, 2000)'},
                               follow=True)
        self.assertEqual(response.json()['veredict'], VeredictCode.RE)
        self.assertEqual(disc_problem.problem_type(), ProblemType.DISC)

    def test_achievements_submit(self):
        """Test to show correct message when obtain an achievement"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        user = create_user('5555', 'tamara')
        ach_submission = NumSubmissionsProblemsAchievementDefinition(name={"es": 'Un envio'},
                                                                      description={
                                                                          "es": 'Envia una solucion para un problema'},
                                                                      num_problems=1, num_submissions=1)
        ach_submission.save()
        ach_submissions = NumSubmissionsProblemsAchievementDefinition(name={"es": 'Tres envios'},
                                                                      description={
                                                                          "es": 'Envia tres soluciones de un problema'},
                                                                      num_problems=1, num_submissions=3)
        ach_submissions.save()
        ach_type = NumSolvedTypeAchievementDefinition(name={"es": 'Es select'},
                                                      description={"es": 'Resuelve un problema SELECT'},
                                                      num_problems=1, problem_type=ProblemType.SELECT.name)
        client.login(username='tamara', password='5555')
        submit_select_url = reverse('judge:submit', args=[select_problem.pk])

        # The user submits one solution and obtains the first achievement
        response = client.post(submit_select_url, {'code': 'MAL'}, follow=True)  # Validation Error, too short
        obtained_achieve = ObtainedAchievement.objects.filter(user=user)
        self.assertIn( obtained_achieve[0].achievement_definition.name['es'], response.json()['achievements'])

        # The user submits a new solution and does not receive any achievement
        response = client.post(submit_select_url, {'code': 'MAL'}, follow=True)  # Validation Error, too short
        self.assertNotIn('achievements', response.json())

        # The user makes another submission and obtain two achievements
        ach_type.save()
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.SELECT_OK)
        collection = create_collection('Coleccion 1')
        select = SelectProblem(zipfile=zip_select_path, collection=collection)
        select.clean()
        select.save()
        submit_url = reverse('judge:submit', args=[select.pk])
        response = client.post(submit_url, {'code': select.solution}, follow=True)
        obtained_achieve = ObtainedAchievement.objects.filter(user=user)
        self.assertIn( obtained_achieve[1].achievement_definition.name['es'], response.json()['achievements'])
        self.assertIn( obtained_achieve[2].achievement_definition.name['es'], response.json()['achievements'])

        # The user submits a new solution and does not receive any achievement
        response = client.post(submit_select_url, {'code': 'MAL'}, follow=True)  # Validation Error, too short
        self.assertNotIn('achievements', response.json())
