# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the feedback module by simulation connections
"""
import os

from django.test import TestCase, Client
import django.contrib.auth
from django.urls import reverse

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

        # download_submission redirects to login
        submission_url = reverse('judge:download_submission', args=[submission.pk])
        login_redirect_submission = f'{login_redirect_url}?next={submission_url}'
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_submission, 302)])

    def test_logged(self):
        """Connections from a logged user"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        user = create_user('5555', 'pepe')
        create_user('1234', 'ana')
        submission = create_submission(problem, user, VeredictCode.AC, 'select *** from *** where *** and more')
        client.login(username='pepe', password='5555')

        collections_url = reverse('judge:collections')
        collection_url = reverse('judge:collection', args=[collection.pk])
        problem_url = reverse('judge:problem', args=[problem.pk])
        no_problem_url = reverse('judge:problem', args=[8888888])
        submit_url = reverse('judge:submit', args=[problem.pk])
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

    def test_show_problems(self):
        """Shows a problem of each type"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.DML_OK)
        zip_function_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.FUNCTIOM_OK)
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
        zip_function_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.FUNCTIOM_OK)
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
