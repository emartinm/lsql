# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the feedback module by simulation connections
"""
import os

from django.test import TestCase, Client
import django.contrib.auth
from django.urls import reverse
from django.contrib.auth.models import Group
from judge.models import Collection, SelectProblem, Submission, FunctionProblem, DMLProblem, ProcProblem, \
    TriggerProblem
from judge.types import VeredictCode
import judge.tests.test_oracle
from judge.tests.test_parse import ParseTest


def create_select_problem(collection, name='Ejemplo'):
    """Creates and stores a Select Problem"""
    create = 'CREATE TABLE test (n NUMBER);'
    insert = "INSERT INTO test VALUES (901)"
    solution = 'SELECT * FROM test'
    problem = SelectProblem(title_md=name, text_md='texto largo',
                            create_sql=create, insert_sql=insert, collection=collection,
                            solution=solution)
    problem.clean()
    problem.save()
    return problem


def create_dml_problem(collection, name='Ejemplo'):
    """Creates and stores a DML Problem accepting between 2 and 3 SQL sentences"""
    create = 'CREATE TABLE test (n NUMBER);'
    insert = "INSERT INTO test VALUES (901)"
    solution = 'INSERT INTO test VALUES (25); INSERT INTO test VALUES (50); INSERT INTO test VALUES (75);'
    problem = DMLProblem(title_md=name, text_md='texto largo',
                         create_sql=create, insert_sql=insert, collection=collection,
                         solution=solution, min_stmt=2, max_stmt=3)
    problem.clean()
    problem.save()
    return problem


def create_collection(name='Prueba'):
    """Creates and stores a collection"""
    collection = Collection(name_md=name, description_md='texto explicativo')
    collection.clean()
    collection.save()
    return collection


def create_user(passwd, username='usuario'):
    """Creates and stores a user"""
    user = django.contrib.auth.get_user_model().objects.create_user(
        username=username,
        email='email@ucm.es',
        password=passwd)
    return user


def create_superuser(passwd, username='staff'):
    """Creates and stores a super user"""
    user = django.contrib.auth.get_user_model().objects.create_superuser(
        username=username,
        password=passwd)
    return user


def create_group(name='nombre'):
    """Creates and stores a group"""
    group = Group.objects.create(name=name)
    return group


def create_submission(problem, user, veredict, code='nada'):
    """Creates and stores a submission"""
    sub = Submission(code=code, veredict_code=veredict, user=user, problem=problem)
    sub.clean()
    sub.save()
    return sub


class ViewsTest(TestCase):
    """Tests for the module views"""

    def test_not_logged(self):
        """Connections from an anonymous user redirects to login"""
        client = Client()
        collection = create_collection()
        problem = create_select_problem(collection)
        user = create_user('1234')
        submission = create_submission(problem, user, VeredictCode.AC)

        collections_url = reverse('judge:collections')
        login_redirect_url = reverse('judge:login')
        login_redirect_collections_url = f'{login_redirect_url}?next={collections_url}'

        # Root redirects to login
        response = client.get('/sql/', follow=True)
        self.assertEqual(response.redirect_chain,
                         [(collections_url, 302),
                          (login_redirect_collections_url, 302)])

        # Collections redirects to login
        response = client.get(collections_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_collections_url, 302)])

        # Collection redirects to login
        collection_url = reverse('judge:collection', args=[collection.pk])
        login_redirect_collection_url = f'{login_redirect_url}?next={collection_url}'
        response = client.get(collection_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_collection_url, 302)])

        # Problem redirects to login
        problem_url = reverse('judge:problem', args=[problem.pk])
        login_redirect_problem = f'{login_redirect_url}?next={problem_url}'
        response = client.get(problem_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_problem, 302)])

        # POST submit redirects to login
        submit_url = reverse('judge:submit', args=[problem.pk])
        login_redirect_submit = f'{login_redirect_url}?next={submit_url}'
        response = client.post(submit_url, {'code': 'SELECT...'}, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_submit, 302)])

        # Submissions redirects to login
        submissions_url = reverse('judge:submissions')
        login_redirect_submissions = f'{login_redirect_url}?next={submissions_url}'
        response = client.get(submissions_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_submissions, 302)])

        # Submission redirects to login
        submission_url = reverse('judge:submission', args=[submission.pk])
        login_redirect_submission = f'{login_redirect_url}?next={submission_url}'
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_submission, 302)])

        # create_insert redirects to login
        create_url = reverse('judge:create_insert', args=[problem.pk])
        login_redirect_create = f'{login_redirect_url}?next={create_url}'
        response = client.get(create_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_create, 302)])

        # results redirects to login
        result_url = reverse('judge:results')
        login_redirect_results = f'{login_redirect_url}?next={result_url}'
        response = client.get(result_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_results, 302)])

    def test_logged(self):
        """Connections from a logged user"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        problem_dml = create_dml_problem(collection, 'DMLProblem')
        user = create_user('5555', 'pepe')
        create_user('1234', 'ana')
        submission = create_submission(problem, user, VeredictCode.AC, 'select *** from *** where *** and more')
        client.login(username='pepe', password='5555')

        collections_url = reverse('judge:collections')
        collection_url = reverse('judge:collection', args=[collection.pk])
        problem_url = reverse('judge:problem', args=[problem.pk])
        no_problem_url = reverse('judge:problem', args=[8888888])
        submit_url = reverse('judge:submit', args=[problem.pk])
        submit_dml_url = reverse('judge:submit', args=[problem_dml.pk])
        submissions_url = reverse('judge:submissions')
        submission_url = reverse('judge:submission', args=[submission.pk])
        pass_done_url = reverse('judge:password_change_done')

        # Root redirects to collection
        response = client.get('/sql/', follow=True)
        self.assertEqual(response.redirect_chain,
                         [(collections_url, 302)])

        # OK and one collection with title
        response = client.get(collections_url, follow=True)
        self.assertTrue(response.status_code == 200 and collection.name_md in str(response.content))

        # OK and one problem in collection
        response = client.get(collection_url, follow=True)
        self.assertTrue(response.status_code == 200 and problem.title_md in str(response.content))

        # OK and title in problem page
        response = client.get(problem_url, follow=True)
        self.assertTrue(response.status_code == 200 and problem.title_md in str(response.content))

        # NotFound
        response = client.get(no_problem_url, follow=True)
        self.assertTrue(response.status_code == 404)

        # JSON with AC
        response = client.post(submit_url, {'code': problem.solution}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.AC)

        # JSON with WA
        response = client.post(submit_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.WA)

        # JSON with VE
        response = client.post(submit_url, {'code': ''}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)

        # JSON with VE
        response = client.post(submit_url, {'code': 'select * from test; select * from test;'},
                               follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)

        # JSON with TLE
        tle = judge.tests.test_oracle.SELECT_TLE
        response = client.post(submit_url, {'code': tle}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.TLE)

        # JSON with RE (table and column do not exist)
        response = client.post(submit_url, {'code': 'SELECT pumba FROM timon'}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.RE)

        # There must be 7 submission to problem
        response = client.get(submissions_url, follow=True)
        html = str(response.content)
        self.assertEqual(html.count(problem.title_md), 7)

        # JSON with VE (new Problem)
        response = client.post(submit_dml_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)

        # There must be 1 submission to new problem
        response = client.get(submissions_url, {'problem_id': problem_dml.pk, 'user_id': user.id}, follow=True)
        html = str(response.content)
        self.assertEqual(html.count(problem_dml.title_md), 1)

        # problem_id is not numeric
        response = client.get(submissions_url, {'problem_id': 'problem', 'user_id': 'user'}, follow=True)
        self.assertTrue(response.status_code == 404 and
                        'El identificador no tiene el formato correcto' in str(response.content))

        # Submission contains user code
        response = client.get(submission_url, follow=True)
        self.assertTrue('select *** from *** where *** and more' in str(response.content))

        # status_code OK
        response = client.get(pass_done_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Only submission from the same user
        client.logout()
        client.login(username='ana', password='1234')
        # Submssion contains user code
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.status_code, 403)
        response = client.get(submissions_url, {'problem_id': problem_dml.pk, 'user_id': user.id}, follow=True)
        self.assertIn('Forbidden', str(response.content))
        client.logout()
        # create a teacher and show submission to user pepe
        teacher = create_superuser('1111', 'teacher')
        client.login(username=teacher.username, password='1111')
        response = client.get(submissions_url, {'problem_id': problem_dml.pk, 'user_id': user.id}, follow=True)
        html = str(response.content)
        self.assertEqual(html.count(problem_dml.title_md), 1)
        client.logout()

    def test_show_problems(self):
        """Shows a problem of each type"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.DML_OK)
        zip_function_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.TRIGGER_OK)

        collection = create_collection('Colleccion de prueba XYZ')
        user = create_user('5555', 'pepe')

        select_problem = SelectProblem(zipfile=zip_select_path, collection=collection, author=user)
        dml_problem = DMLProblem(zipfile=zip_dml_path, collection=collection, author=user)
        function_problem = FunctionProblem(zipfile=zip_function_path, collection=collection, author=user)
        proc_problem = ProcProblem(zipfile=zip_proc_path, collection=collection, author=user)
        trigger_problem = TriggerProblem(zipfile=zip_trigger_path, collection=collection, author=user)

        client = Client()
        client.login(username='pepe', password='5555')

        for problem in [select_problem, dml_problem, function_problem, proc_problem, trigger_problem]:
            problem.clean()
            problem.save()
            problem_url = reverse('judge:problem', args=[problem.pk])
            response = client.get(problem_url, follow=True)
            self.assertTrue(response.status_code == 200 and problem.title_md in str(response.content))

    def test_download(self):
        """Download the script of a problem (CREATE + INSERT)"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.DML_OK)
        zip_function_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.TRIGGER_OK)

        collection = create_collection('Colleccion de prueba AAA')
        user = create_user('54522', 'antonio')

        select_problem = SelectProblem(zipfile=zip_select_path, collection=collection, author=user)
        dml_problem = DMLProblem(zipfile=zip_dml_path, collection=collection, author=user)
        function_problem = FunctionProblem(zipfile=zip_function_path, collection=collection, author=user)
        proc_problem = ProcProblem(zipfile=zip_proc_path, collection=collection, author=user)
        trigger_problem = TriggerProblem(zipfile=zip_trigger_path, collection=collection, author=user)

        client = Client()
        client.login(username='antonio', password='54522')

        for problem in [select_problem, dml_problem, function_problem, proc_problem, trigger_problem]:
            problem.clean()
            problem.save()
            url = reverse('judge:create_insert', args=[problem.pk])
            response = client.get(url, follow=True)
            script = problem.create_sql + '\n\n' + problem.insert_sql

            self.assertEqual(
                response.get('Content-Disposition'),
                "attachment; filename=create_insert.sql",
            )
            self.assertEqual(
                response.get('Content-Type'),
                "application/sql"
            )
            self.assertEqual(response.content.decode('UTF-8'), script)

            self.assertTrue(response.status_code == 200)

    def test_show_result_classification(self):
        """test to show the classification"""
        client = Client()
        # Create 1 collection
        collection = create_collection('Coleccion 1')
        # Create 2 problems
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        dml_problem = create_dml_problem(collection, 'insert a Number')
        select_problem_2 = create_select_problem(collection, 'SelectProblem 2 DEF ABC')
        # Create 3 users (2 students y 1 professor)

        user_1 = create_user('12345', 'pepe')
        user_2 = create_user('12345', 'ana')
        teacher = create_superuser('12345', 'iker')
        group_a = create_group('1A')
        group_b = create_group('1B')
        # add to group a all and to group b only the teacher
        group_a.user_set.add(user_1)
        group_a.user_set.add(user_2)
        group_a.user_set.add(teacher)

        group_b.user_set.add(teacher)

        # use the teacher to view the two groups
        client.login(username=teacher.username, password='12345')
        classification_url = reverse('judge:result', args=[collection.pk])
        submit_select_url = reverse('judge:submit', args=[select_problem.pk])
        submit_select_2_url = reverse('judge:submit', args=[select_problem_2.pk])
        submit_dml_url = reverse('judge:submit', args=[dml_problem.pk])
        # I see group b where there is only the teacher
        # the table is empty because there is only the teacher
        response = client.get(classification_url, {'group': group_b.id}, follow=True)
        self.assertEqual(response.status_code,200)
        self.assertTrue(user_2.username not in str(response.content) and  user_1.username not in str(response.content))

        # I find that there are two exercises in the collection
        self.assertIn(select_problem.title_md, str(response.content))
        self.assertIn(dml_problem.title_md, str(response.content))
        self.assertIn(select_problem_2.title_md, str(response.content))

        # I look at the group to where the students are
        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertIn(user_1.username, str(response.content))
        self.assertIn(user_2.username, str(response.content))

        # I am connected to a non-existent group
        response = client.get(classification_url, {'group': 999}, follow=True)
        self.assertEqual(response.status_code, 404)

        response = client.get(classification_url, follow=True)
        self.assertTrue(user_1.username, str(response.content))
        self.assertIn(user_2.username, str(response.content))

        # I connect to a non-numeric group
        response = client.get(classification_url, {'group': '1A'}, follow=True)
        msg = 'El identificador de grupo no tiene el formato correcto'
        self.assertTrue(response.status_code == 404 and msg in str(response.content))
        client.logout()
        client.login(username=user_1.username, password='12345')

        # I connect to pepe at 1b
        response = client.get(classification_url, {'group': group_b.id}, follow=True)
        self.assertEqual(response.status_code, 403)

        client.post(submit_select_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        client.post(submit_select_url, {'code': select_problem.solution}, follow=True)

        client.post(submit_dml_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        client.post(submit_dml_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        client.post(submit_dml_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        client.post(submit_dml_url, {'code': dml_problem.solution}, follow=True)

        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertIn('1/2 (2)', str(response.content))
        self.assertIn('1/4 (4)', str(response.content))
        self.assertIn('6', str(response.content))

        client.logout()
        client.login(username=user_2.username, password='12345')

        client.post(submit_select_url, {'code': select_problem.solution}, follow=True)
        client.post(submit_select_url, {'code': select_problem.solution}, follow=True)
        client.post(submit_select_url, {'code': select_problem.solution}, follow=True)

        client.post(submit_dml_url, {'code': 'Select * from test'}, follow=True)
        client.post(submit_dml_url, {'code': 'Select * from test'}, follow=True)
        client.post(submit_dml_url, {'code': dml_problem.solution}, follow=True)

        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertIn('3/3 (1)', str(response.content))
        self.assertIn('1/3 (3)', str(response.content))
        self.assertIn('4', str(response.content))

        # ana's position is better than pepe's position
        index_ana = str(response.content).index('ana')
        index_pepe = str(response.content).index('pepe')
        self.assertTrue(index_ana < index_pepe)

        client.post(submit_select_2_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertIn('0/1 (1)', str(response.content))

        client.logout()

    def test_show_result(self):
        """Test to enter the results page where you can see the collections."""
        client = Client()
        # Create 2 collections
        collection = create_collection('Coleccion 1')
        collection_2 = create_collection('Coleccion 2')
        # Create 2 useres
        user = create_user('123456', 'pepe')
        user2 = create_user('123456', 'ana')
        # create 1 group  and assign it to a user
        group = create_group('1A')
        group.user_set.add(user)
        result_url = reverse('judge:results')
        # user with group can view the page results
        client.login(username=user.username, password='123456')

        response = client.get(result_url, follow=True)
        title = 'Colecciones'
        self.assertEqual(response.status_code, 200)
        self.assertIn(collection.name_md, str(response.content))
        self.assertIn(collection_2.name_md, str(response.content))
        self.assertIn(title, str(response.content))
        client.logout()
        # the user without a group can't see the page results
        client.login(username=user2.username, password='123456')
        response = client.get(result_url, follow=True)
        msg = 'Lo sentimos! No tienes asignado un grupo de la asignatura'
        msg1 = 'Por favor, contacta con tu profesor para te asignen un grupo de clase.'
        self.assertEqual(response.status_code, 200)
        self.assertTrue(msg1 in str(response.content) and msg in str(response.content))
        client.logout()
        # I connect with a teacher without groups
        teacher = create_superuser('12345','teacher')
        client.login(username=teacher.username, password='12345')
        response = client.get(result_url, follow=True)
        self.assertEqual(response.status_code, 200)

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
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)
        self.assertIn('exactamente 1 sentencia SQL', response.json()['message'])

        # JSON with VE and correct message for 1--3 SQL
        stmt = 'INSERT INTO test VALUES (25);'
        response = client.post(submit_url_dml, {'code': stmt}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)
        self.assertIn('entre 2 y 3 sentencias SQL', response.json()['message'])

        stmt = 'INSERT INTO test VALUES (25); INSERT INTO test VALUES (50); INSERT INTO test VALUES (75);' \
               'INSERT INTO test VALUES (100);'
        response = client.post(submit_url_dml, {'code': stmt}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)
        self.assertIn('entre 2 y 3 sentencias SQL', response.json()['message'])

        # JSON with VE and correct message for less than 10 characters
        stmt = 'holis'
        response = client.post(submit_url_dml, {'code': stmt}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)
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
            self.assertTrue(response.json()['veredict'] == VeredictCode.WA)
            self.assertIn('Generado por tu código SQL: 0 columnas', response.json()['feedback'])
