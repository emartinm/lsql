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

        # Root redirects to login
        response = client.get('/sql/', follow=True)
        self.assertEqual(response.redirect_chain,
                         [('/sql/collection/', 302),
                          ('/sql/login?next=/sql/collection/', 302),
                          ('/sql/login/?next=%2Fsql%2Fcollection%2F', 301)])

        # /sql/collection redirects to login
        response = client.get('/sql/collection/', follow=True)
        self.assertEqual(response.redirect_chain,
                         [('/sql/login?next=/sql/collection/', 302),
                          ('/sql/login/?next=%2Fsql%2Fcollection%2F', 301)])

        # /sql/collection/X redirects to login
        response = client.get(f'/sql/collection/{collection.pk}', follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/login'))

        # /sql/problem/X redirects to login
        response = client.get(f'/sql/problem/{problem.pk}', follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/login'))

        # POST /sql/submit/X redirects to login
        response = client.post(f'/sql/submit/{problem.pk}', {'code': 'SELECT...'}, follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/login'))

        # /sql/submission redirects to login
        response = client.get('/sql/submission/', follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/login'))

        # /sql/submission/X redirects to login
        response = client.get(f'/sql/submission/{submission.pk}', follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/login'))

        # /sql/problem/X/create_insert redirects to login
        url = reverse('judge:create_insert', args=[problem.pk])
        response = client.get(url, follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/login'))

    def test_logged(self):
        """Connections from a logged user"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        user = create_user('5555', 'pepe')
        create_user('1234', 'ana')
        submission = create_submission(problem, user, VeredictCode.AC, 'select *** from *** where *** and more')
        client.login(username='pepe', password='5555')

        # Root redirects to collection
        response = client.get('/sql/', follow=True)
        self.assertTrue(response.redirect_chain[0][0].startswith('/sql/collection'))

        # OK and one collection with title
        response = client.get('/sql/collection/', follow=True)
        self.assertTrue(response.status_code == 200 and collection.name_md in str(response.content))

        # OK and one problem
        response = client.get(f'/sql/collection/{collection.pk}', follow=True)
        self.assertTrue(response.status_code == 200 and problem.title_md in str(response.content))

        # OK and title in page
        response = client.get(f'/sql/problem/{problem.pk}', follow=True)
        self.assertTrue(response.status_code == 200 and problem.title_md in str(response.content))

        # NotFound
        response = client.get('/sql/problem/888888', follow=True)
        self.assertTrue(response.status_code == 404)

        # JSON with AC
        response = client.post(f'/sql/submit/{problem.pk}', {'code': problem.solution}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.AC)

        # JSON with WA
        response = client.post(f'/sql/submit/{problem.pk}', {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.WA)

        # JSON with VE
        response = client.post(f'/sql/submit/{problem.pk}', {'code': ''}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)

        # JSON with VE
        response = client.post(f'/sql/submit/{problem.pk}', {'code': 'select * from test; select * from test;'},
                               follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.VE)

        # JSON with TLE
        tle = judge.tests.test_oracle.SELECT_TLE
        response = client.post(f'/sql/submit/{problem.pk}', {'code': tle}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.TLE)

        # JSON with RE (table and column do not exist)
        response = client.post(f'/sql/submit/{problem.pk}', {'code': 'SELECT pumba FROM timon'}, follow=True)
        self.assertTrue(response.json()['veredict'] == VeredictCode.RE)

        # There must be 5 submission to problem
        response = client.get('/sql/submission/', follow=True)
        html = str(response.content)
        self.assertEqual(html.count(problem.title_md), 7)

        # Submssion contains user code
        response = client.get(f'/sql/submission/{submission.pk}', follow=True)
        self.assertTrue('select *** from *** where *** and more' in str(response.content))

        # status_code OK
        response = client.get('/sql/password_change_done/', follow=True)
        self.assertEqual(response.status_code, 200)

        # Only submission from the same user
        client.logout()
        client.login(username='ana', password='1234')
        # Submssion contains user code
        response = client.get(f'/sql/submission/{submission.pk}', follow=True)
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
            response = client.get(f'/sql/problem/{problem.pk}', follow=True)
            self.assertTrue(response.status_code == 200 and problem.title_md in str(response.content))

    def test_download(self):
        """Download a script to problem"""
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
            script = problem.create_sql + '\n' + problem.insert_sql

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
