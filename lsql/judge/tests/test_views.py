# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the feedback module by simulation connections
"""
from datetime import datetime
import os

from django.test import TestCase, Client
from django.urls import reverse

from judge.models import SelectProblem, Submission, FunctionProblem, DMLProblem, ProcProblem, TriggerProblem
from judge.types import VerdictCode
import judge.tests.test_oracle
from judge.views import first_day_of_course
from judge.feedback import filter_expected_db
from judge.tests.test_common import create_user, create_superuser, create_group, create_collection, \
    create_select_problem, create_submission, create_dml_problem, create_dml_complete_problem, TestPaths


class ViewsTest(TestCase):
    """Tests for the module views"""

    def test_not_logged(self):
        """Connections from an anonymous user redirects to login"""
        client = Client()
        collection = create_collection()
        problem = create_select_problem(collection)
        user = create_user('1234')
        submission = create_submission(problem, user, VerdictCode.AC)

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
        user = create_user('5555', 'pepe')
        create_user('1234', 'ana')
        collection = create_collection('Colleccion de prueba XYZ', author=create_superuser('0000', 'the_teacher'))
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        problem_dml = create_dml_problem(collection, 'DMLProblem')
        submission = create_submission(problem, user, VerdictCode.AC, 'select *** from *** where *** and more')
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
        self.assertEqual(response.redirect_chain, [(collections_url, 302)])

        # OK and one collection with title
        response = client.get(collections_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(collection.name_html, response.content.decode('utf-8'))

        # OK and one problem in collection
        response = client.get(collection_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(problem.title_html, response.content.decode('utf-8'))

        # OK and title in problem page
        response = client.get(problem_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(problem.title_html, response.content.decode('utf-8'))

        # NotFound
        response = client.get(no_problem_url, follow=True)
        self.assertEqual(response.status_code, 404)

        # JSON with AC
        response = client.post(submit_url, {'code': problem.solution}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.AC)

        # JSON with WA
        response = client.post(submit_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.WA)

        # JSON with VE
        response = client.post(submit_url, {'code': ''}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.VE)

        # JSON with VE
        response = client.post(submit_url, {'code': 'select * from test; select * from test;'}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.VE)

        # JSON with TLE
        tle = judge.tests.test_oracle.SELECT_TLE
        response = client.post(submit_url, {'code': tle}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.TLE)

        # JSON with RE (table and column do not exist)
        response = client.post(submit_url, {'code': 'SELECT pumba FROM timon'}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.RE)

        # There must be 7 submission to problem
        response = client.get(submissions_url, follow=True)
        self.assertEqual(response.content.decode('utf-8').count(problem.title_html), 7)

        # JSON with VE (new Problem)
        response = client.post(submit_dml_url, {'code': 'SELECT * FROM test where n = 1000'}, follow=True)
        self.assertEqual(response.json()['verdict'], VerdictCode.VE)

        # There must be 1 submission to new problem
        response = client.get(submissions_url, {'problem_id': problem_dml.pk, 'user_id': user.id}, follow=True)
        self.assertEqual(response.content.decode('utf-8').count(problem_dml.title_html), 1)

        # problem_id is not numeric
        response = client.get(submissions_url, {'problem_id': 'problem', 'user_id': 'user'}, follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Introduzca un número entero', response.content.decode('utf-8'))

        # Submission contains user code
        response = client.get(submission_url, follow=True)
        self.assertIn('select *** from *** where *** and more', response.content.decode('utf-8'))

        # status_code OK
        response = client.get(pass_done_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Only submission from the same user
        client.logout()
        client.login(username='ana', password='1234')
        # Submission contains user code
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.status_code, 403)
        response = client.get(submissions_url, {'problem_id': problem_dml.pk, 'user_id': user.id}, follow=True)
        self.assertIn('Forbidden', response.content.decode('utf-8'))
        client.logout()
        # create a teacher and show submission to user pepe
        teacher = create_superuser('1111', 'teacher')
        client.login(username=teacher.username, password='1111')
        response = client.get(submissions_url, {
            'problem_id': problem_dml.pk, 'user_id': user.id,
            'start': first_day_of_course(datetime(2020, 9, 1)).strftime('%Y-%m-%d'),
            'end': datetime.today().strftime('%Y-%m-%d')},
                              follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8').count(problem_dml.title_html), 1)
        client.logout()

    def test_visibility_submission(self):
        """Checks that only the owner and superusers can see the submission details"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        user = create_user('5555', 'pepe')
        create_superuser('aaaa', 'mr_teacher')
        create_user('1234', 'ana')
        submission = create_submission(problem, user, VerdictCode.AC, 'select *** from *** where *** and more')
        submission_url = reverse('judge:submission', args=[submission.pk])

        # The same user can access submission details
        client.login(username='pepe', password='5555')
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('select *** from *** where *** and more', response.content.decode('utf-8'))
        client.logout()

        # A teacher can access submission details from a different user
        client.login(username='mr_teacher', password='aaaa')
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('select *** from *** where *** and more', response.content.decode('utf-8'))
        client.logout()

        # Non-teacher user cannot access submission details from a different user
        client.login(username='ana', password='1234')
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Forbidden', response.content.decode('utf-8'))
        client.logout()

    def test_show_problems(self):
        """Shows a problem of each type"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.SELECT_OK)
        zip_dml_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.DML_OK)
        zip_function_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.PROC_OK)
        zip_trigger_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.TRIGGER_OK)

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
            self.assertEqual(response.status_code, 200)
            self.assertIn(problem.title_html, response.content.decode('utf-8'))

    def test_download(self):
        """Download the script of a problem (CREATE + INSERT)"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.SELECT_OK)
        zip_dml_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.DML_OK)
        zip_function_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.PROC_OK)
        zip_trigger_path = os.path.join(curr_path,  TestPaths.ZIP_FOLDER,  TestPaths.TRIGGER_OK)

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

            self.assertEqual(response.status_code, 200)

    def test_show_result_classification_date(self):
        """ test to show the classification with dates """
        client = Client()
        submissions_url = reverse('judge:submissions')

        # Create 1 collection
        collection = create_collection('Collection 1')
        classification_url = reverse('judge:result', args=[collection.pk])
        # Create 1 problem
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        # Create 3 users (2 students y 1 professor)
        user_1 = create_user('12345', 'pepe')
        user_2 = create_user('12345', 'ana')
        teacher = create_superuser('12345', 'iker')

        # Create 2 groups
        group_a = create_group('1A')
        group_b = create_group('1B')

        # add the students and the teacher to the group a, and only user 2 to group B
        group_a.user_set.add(user_1)
        group_a.user_set.add(user_2)
        group_a.user_set.add(teacher)
        group_b.user_set.add(user_2)

        # create course start date and today's date
        start = first_day_of_course(datetime(2020, 9, 1)).strftime('%Y-%m-%d')
        end = datetime(2021, 3, 7).strftime('%Y-%m-%d')

        # I connect to a student and in the URL I insert dates
        client.login(username=user_1.username, password='12345')
        # the first student makes three submissions (1/3 (3))
        sub1 = Submission.objects.create(code='SELECT * FROM test where n = 1000',
                                         user=user_1, verdict_code=VerdictCode.WA, problem=select_problem)
        sub1.save()
        Submission.objects.filter(id=sub1.id).update(creation_date=datetime(2021, 3, 5))
        sub2 = Submission.objects.create(code='SELECT * FROM test where n = 1000',
                                         user=user_1, verdict_code=VerdictCode.WA, problem=select_problem)
        sub2.save()
        Submission.objects.filter(id=sub2.id).update(creation_date=datetime(2021, 3, 5))
        sub3 = Submission.objects.create(code=select_problem.solution,
                                         user=user_1, verdict_code=VerdictCode.AC, problem=select_problem)
        sub3.save()
        Submission.objects.filter(id=sub3.id).update(creation_date=datetime(2021, 3, 7))

        client.logout()
        client.login(username=user_2.username, password='12345')
        # the second student makes two submissions (1/2 (1))
        sub4 = Submission.objects.create(code=select_problem.solution,
                                         user=user_2, verdict_code=VerdictCode.AC, problem=select_problem)
        sub4.save()
        Submission.objects.filter(id=sub4.id).update(creation_date=datetime(2021, 3, 7, 17, 45))
        sub5 = Submission.objects.create(code='SELECT * FROM test where n = 1000',
                                         user=user_2, verdict_code=VerdictCode.WA, problem=select_problem)
        sub5.save()
        Submission.objects.filter(id=sub5.id).update(creation_date=datetime(2021, 3, 7, 18, 22))
        response = client.get(submissions_url, {'problem_id': select_problem.pk, 'user_id': user_2.id,
                                                'start': first_day_of_course(datetime(2020, 9, 1)).strftime('%Y-%m-%d'),
                                                'end': datetime(2021, 3, 7).strftime('%Y-%m-%d')},
                              follow=True)
        self.assertIn('7 de Marzo de 2021 a las 17:45', response.content.decode('utf-8'))
        self.assertIn('7 de Marzo de 2021 a las 18:22', response.content.decode('utf-8'))
        client.logout()

        client.login(username=teacher.username, password='12345')
        response = client.get(classification_url, {
            'group': group_a.id, 'start': start, 'end': end}, follow=True)
        self.assertIn(user_2.username, response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(user_2.username, response.content.decode('utf-8'))
        self.assertIn(user_1.username, response.content.decode('utf-8'))
        for fragment in ['1/3 (3)', '3', '1', '1/2 (1)']:
            self.assertIn(fragment, response.content.decode('utf-8'))
        last_end_date = datetime(2021, 3, 5).strftime('%Y-%m-%d')
        # For yesterday's date student one must have two failed submissions and no correct submissions 0/2 (2)
        response = client.get(classification_url, {
            'group': group_a.id, 'start': start, 'end': last_end_date}, follow=True)
        for fragment in ['0/2', '0', '0', '0/0']:
            self.assertIn(fragment, response.content.decode('utf-8'))

        # Incorrect dates
        good_start_date = datetime(2019, 9, 1).strftime('%Y-%m-%d')
        wrong_end_date = datetime(2222, 2, 2).strftime('%Y-%m-%d')
        response = client.get(classification_url, {
            'group': group_a.id, 'start': end, 'end': start}, follow=True)
        self.assertIn('¡Error! La fecha inicial no puede ser mayor que la fecha final.',
                      response.content.decode('utf-8'))
        response = client.get(classification_url, {
            'group': group_a.id, 'start': good_start_date, 'end': end}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {
            'group': group_a.id, 'start': start, 'end': wrong_end_date}, follow=True)
        self.assertIn("¡Error! La fecha final no puede ser mayor que la fecha de hoy.",
                      response.content.decode('utf-8'))

        response = client.get(classification_url, {
            'group': group_a.id, 'start': 'eee', 'end': end}, follow=True)
        self.assertIn("Introduzca una fecha válida", response.content.decode('utf-8'))

        response = client.get(classification_url, {
            'group': group_a.id, 'start': start, 'end': start}, follow=True)
        for fragment in ['0/0 (0)', '0', '0']:
            self.assertIn(fragment, response.content.decode('utf-8'))

    def test_permission_ranking(self):
        """ Test to access the ranking from different groups """
        # Create 1 collection with 1 problem
        collection = create_collection('Coleccion 1')
        classification_url = reverse('judge:result', args=[collection.pk])

        # Create 3 users (2 students y 1 staff)
        user_1 = create_user('12345', 'pepe')
        user_2 = create_user('12345', 'ana')
        teacher = create_superuser('12345', 'iker')

        # Create 2 groups
        group_b = create_group('1B')
        group_a = create_group('1A')

        # add the students and the teacher to the group a, and only user 2 to group B
        group_a.user_set.add(user_1)
        group_a.user_set.add(user_2)
        group_a.user_set.add(teacher)
        group_b.user_set.add(user_2)

        # create course start date and today's date
        start = first_day_of_course(datetime(2020, 9, 1)).strftime('%Y-%m-%d')
        end = datetime(2021, 3, 7).strftime('%Y-%m-%d')

        # Checks access to rankings: 'pepe' only to group A, 'ana' to group A and B,
        # 'iker' also to both groups as staff
        client = Client()
        client.login(username='pepe', password='12345')
        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {'group': group_b.id}, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Forbidden', response.content.decode('utf-8'))
        response = client.get(classification_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('1A', response.content.decode('utf-8'))
        client.logout()

        client.login(username='ana', password='12345')
        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {'group': group_b.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('1B', response.content.decode('utf-8'))
        client.logout()

        client.login(username='iker', password='12345')
        response = client.get(classification_url, {'group': group_a.id, 'start': start, 'end': end}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {'group': group_b.id, 'start': start, 'end': end}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {'group': group_a.id, 'end': end}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {'group': group_b.id, 'start': start}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, {'group': group_b.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(classification_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('1B', response.content.decode('utf-8'))
        client.logout()

    def test_first_day_of_course(self):
        """Test that given a date returns you on the first day of the academic year"""
        #
        self.assertEqual(datetime(2020, 9, 1), first_day_of_course(datetime(2020, 10, 2)))
        self.assertEqual(datetime(2020, 9, 1), first_day_of_course(datetime(2020, 9, 1)))
        self.assertEqual(datetime(2019, 9, 1, 0, 0), first_day_of_course(datetime(2020, 3, 2)))
        self.assertEqual(datetime(2020, 9, 1, 0, 0), first_day_of_course(datetime(2021, 7, 25)))
        self.assertEqual(datetime(2021, 9, 1, 0, 0), first_day_of_course(datetime(2021, 9, 5)))
        self.assertEqual(datetime(2020, 9, 1, 0, 0), first_day_of_course(datetime(2021, 8, 31)))
        self.assertEqual(datetime(2023, 9, 1, 0, 0), first_day_of_course(datetime(2024, 2, 29)))
        self.assertEqual(datetime(2002, 9, 1, 0, 0), first_day_of_course(datetime(2003, 1, 29)))
        self.assertEqual(datetime(2035, 9, 1, 0, 0), first_day_of_course(datetime(2035, 10, 22)))

    def test_show_result_classification(self):
        """ Ranking is correct """
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
        start = first_day_of_course(datetime(2020, 9, 1)).strftime('%Y-%m-%d')
        end = datetime.today().strftime('%Y-%m-%d')
        # use the teacher to view the two groups
        client.login(username=teacher.username, password='12345')
        classification_url = reverse('judge:result', args=[collection.pk])
        # I see group b where there is only the teacher
        # the table is empty because there is only the teacher
        response = client.get(classification_url, {
            'group': group_b.id, 'start': start, 'end': end}, follow=True)
        html = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(user_2.username, html)
        self.assertNotIn(user_1.username, html)

        # I find that there are two exercises in the collection
        self.assertIn(select_problem.title_html, html)
        self.assertIn(dml_problem.title_html, html)
        self.assertIn(select_problem_2.title_html, html)

        # I look at the group to where the students are
        response = client.get(classification_url,
                              {'group': group_a.id, 'start': start, 'end': end}, follow=True)
        self.assertIn(user_1.username, response.content.decode('utf-8'))
        self.assertIn(user_2.username, response.content.decode('utf-8'))

        # I am connected to a non-existent group
        response = client.get(classification_url,
                              {'group': 999, 'start': start, 'end': end}, follow=True)
        self.assertEqual(response.status_code, 404)

        # I connect to a non-numeric group
        response = client.get(classification_url,
                              {'group': '1A', 'start': start, 'end': end}, follow=True)
        msg = 'Introduzca un número entero'
        self.assertEqual(response.status_code, 404)
        self.assertIn(msg, response.content.decode('utf-8'))
        client.logout()

        # I connect to pepe at 1b
        client.login(username=user_1.username, password='12345')
        response = client.get(classification_url, {'group': 'patato'}, follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Introduzca un número entero', response.content.decode('utf_8'))
        response = client.get(classification_url, {'group': group_b.id}, follow=True)
        self.assertEqual(response.status_code, 403)

        Submission.objects.create(problem=select_problem, code='  ', verdict_code=VerdictCode.WA, user=user_1)
        Submission.objects.create(problem=select_problem, code='  ', verdict_code=VerdictCode.WA, user=user_1)
        Submission.objects.create(problem=select_problem, code='  ', verdict_code=VerdictCode.AC, user=user_1)
        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.WA, user=user_1)
        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.WA, user=user_1)
        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.WA, user=user_1)
        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.AC, user=user_1)

        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        for expected in ['1/3 (3)', '1/4 (4)', '7', '2']:
            self.assertIn(expected, response.content.decode('utf-8'))

        client.logout()
        client.login(username=user_2.username, password='12345')

        Submission.objects.create(problem=select_problem, code='  ', verdict_code=VerdictCode.AC, user=user_2)
        Submission.objects.create(problem=select_problem, code='  ', verdict_code=VerdictCode.AC, user=user_2)
        Submission.objects.create(problem=select_problem, code='  ', verdict_code=VerdictCode.AC, user=user_2)

        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.WA, user=user_2)
        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.WA, user=user_2)
        Submission.objects.create(problem=dml_problem, code='  ', verdict_code=VerdictCode.AC, user=user_2)

        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        html = response.content.decode('utf-8')
        for fragment in ['3/3 (1)', '1/3 (3)', '4']:
            self.assertIn(fragment, html)

        # ana's position is better than pepe's position
        self.assertLess(html.index('ana'), html.index('pepe'))

        Submission.objects.create(problem=select_problem_2, code='  ', verdict_code=VerdictCode.WA, user=user_2)
        response = client.get(classification_url, {'group': group_a.id}, follow=True)
        self.assertIn('0/1', response.content.decode('utf-8'))

        client.logout()

    def test_show_result(self):
        """ Test to enter the results page where you can see the collections """
        client = Client()
        # Create 2 collections
        collection = create_collection('Coleccion 1')
        collection_2 = create_collection('Coleccion 2')
        # Create 2 users
        user = create_user('123456', 'pepe')
        create_user('123456', 'ana')
        # create 1 group  and assign it to a user
        group = create_group('1A')
        group.user_set.add(user)
        result_url = reverse('judge:results')
        # user with group can view the page results
        client.login(username=user.username, password='123456')

        response = client.get(result_url, follow=True)
        title = 'Colecciones'
        self.assertEqual(response.status_code, 200)
        self.assertIn(collection.name_html, response.content.decode('utf-8'))
        self.assertIn(collection_2.name_html, response.content.decode('utf-8'))
        self.assertIn(title, response.content.decode('utf-8'))
        client.logout()

        # I connect with a teacher without groups
        teacher = create_superuser('12345', 'teacher')
        client.login(username=teacher.username, password='12345')
        response = client.get(result_url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_results_no_groups(self):
        """ The system does not crash if there are not groups defined """
        client = Client()
        # Create 2 collections
        collection = create_collection('Coleccion 1')
        # Create 1 user and 1 superuser
        user = create_user('123456', 'pepe')
        teacher = create_superuser('12345', 'teacher')
        # URL for connections
        result_url = reverse('judge:results')
        classification_url = reverse('judge:result', args=[collection.pk])

        client.login(username=user.username, password='123456')
        for url in [result_url, classification_url]:
            response = client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        client.logout()

        client.login(username=teacher.username, password='12345')
        for url in [result_url, classification_url]:
            response = client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)

    def test_download_submission(self):
        """ Test to download code of submission """
        client = Client()
        user = create_user('2222', 'tamara')
        create_user('3333', 'juan')
        teacher = create_superuser('1111', 'teacher')
        login_redirect_url = reverse('judge:login')
        collection = create_collection('Colleccion de prueba TTT')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        submission = create_submission(problem, user, VerdictCode.AC, 'select *** from *** where *** and more')

        # Submission redirects to login
        submission_url = reverse('judge:submission', args=[submission.pk])
        login_redirect_submission = f'{login_redirect_url}?next={submission_url}'
        response = client.get(submission_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_submission, 302)])

        # Download your own code submission
        client.login(username='tamara', password='2222')
        url = reverse('judge:download_submission', args=[submission.pk])
        response = client.get(url, follow=True)
        self.assertEqual(
            response.get('Content-Disposition'),
            "attachment; filename=code.sql",
        )
        self.assertEqual(
            response.get('Content-Type'),
            "application/sql"
        )
        self.assertEqual(response.content.decode('UTF-8'), submission.code)

        # Download code submission from another user
        client.logout()
        client.login(username='juan', password='3333')
        response = client.get(url, follow=True)
        self.assertIn('Forbidden', response.content.decode('UTF-8'))

        # Superuser download code submission
        client.logout()
        client.login(username=teacher.username, password='1111')
        url = reverse('judge:download_submission', args=[submission.pk])
        response = client.get(url, follow=True)
        self.assertEqual(
            response.get('Content-Disposition'),
            "attachment; filename=code.sql",
        )
        self.assertEqual(
            response.get('Content-Type'),
            "application/sql"
        )
        self.assertEqual(response.content.decode('UTF-8'), submission.code)

    def test_error_500(self):
        """Test that test_error_500/ generates error 404 for users and raises exception for staff"""
        client = Client()
        create_user('2222', 'tamara')
        create_superuser('1111', 'teacher')
        error_500_rul = reverse('judge:test_error_500')

        # Unauthenticated users obtain the login page
        response = client.get(error_500_rul, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Entrar", response.content.decode('utf_8'))

        # Students obtain 404
        client.login(username='tamara', password='2222')
        response = client.get(error_500_rul, follow=True)
        self.assertEqual(response.status_code, 404)
        client.logout()

        # Staff raises exception (will generate error 500)
        client.login(username='teacher', password='1111')
        with self.assertRaises(IndexError, msg='list index out of range'):
            client.get(error_500_rul, follow=True)
        client.logout()

    def test_filter_expected_db(self):
        """Test for filter an expected db and transform for another to show"""
        initial = {'ESTA SE BORRA': {'rows': [['11111X', 'Real', 'Concha', 70000]],
                                     'header': [['CIF', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                ['NOMBRE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                ['SEDE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                ['NUM_SOCIOS', '<cx_Oracle.DbType DB_TYPE_NUMBER>']]},
                   'ESTA SE MODIFICA': {'rows': [['111X', '222X', '004X']],
                                        'header': [['CIF_LOCAL', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                   ['CIF_VISITANTE', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                   ['NIF', '<cx_Oracle.DbType DB_TYPE_CHAR>']]},
                   'ESTA SE QUEDA IGUAL': {'rows': [['111X', '222X', '004X']],
                                           'header': [['CIF_LOCAL', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                      ['CIF_VISITANTE', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                      ['NIF', '<cx_Oracle.DbType DB_TYPE_CHAR>']]}}
        expected = {'ESTA SE AGREGA': {'rows': [['11111X', 'Gandia', 'Guillermo Olague', 70000]],
                                       'header': [['CIF', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                  ['NOMBRE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                  ['SEDE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                  ['NUM_SOCIOS', '<cx_Oracle.DbType DB_TYPE_NUMBER>']]},
                    'ESTA SE MODIFICA': {'rows': [['111X', '333X', '004X']],
                                         'header': [['CIF_LOCAL', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                    ['CIF_VISITANTE', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                    ['NIF', '<cx_Oracle.DbType DB_TYPE_CHAR>']]},
                    'ESTA SE QUEDA IGUAL': {'rows': [['111X', '222X', '004X']],
                                            'header': [['CIF_LOCAL', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                       ['CIF_VISITANTE', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                       ['NIF', '<cx_Oracle.DbType DB_TYPE_CHAR>']]}}
        result_added = {'ESTA SE AGREGA': {'rows': [['11111X', 'Gandia', 'Guillermo Olague', 70000]],
                                           'header': [['CIF', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                      ['NOMBRE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                      ['SEDE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                      ['NUM_SOCIOS', '<cx_Oracle.DbType DB_TYPE_NUMBER>']]}}
        result_modified = {'ESTA SE MODIFICA': {'rows': [['111X', '333X', '004X']],
                                                'header': [['CIF_LOCAL', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                           ['CIF_VISITANTE', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                           ['NIF', '<cx_Oracle.DbType DB_TYPE_CHAR>']]}}
        result_removed = {'ESTA SE BORRA': {'rows': [['11111X', 'Real', 'Concha', 70000]],
                                            'header': [['CIF', '<cx_Oracle.DbType DB_TYPE_CHAR>'],
                                                       ['NOMBRE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                       ['SEDE', '<cx_Oracle.DbType DB_TYPE_VARCHAR>'],
                                                       ['NUM_SOCIOS', '<cx_Oracle.DbType DB_TYPE_NUMBER>']]}}
        ret_1, ret_2, ret_3 = filter_expected_db(expected, initial)
        self.assertEqual(ret_1, result_added)
        self.assertEqual(ret_2, result_modified)
        self.assertEqual(ret_3, result_removed)

    def test_expected_results_view(self):
        """Test for the view when show an expected result with tables"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        dml_problem = create_dml_complete_problem(collection, 'random')

        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')

        problem_url = reverse('judge:problem', args=[dml_problem.pk])
        response = client.get(problem_url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('TEST_TABLE_1 (Tabla modificada)', content)
        self.assertIn('TEST_TABLE_2 (Tabla eliminada)', content)
        self.assertIn('TEST_TABLE_3 (Tabla modificada)', content)
        self.assertIn('NEW (Tabla añadida)', content)

    def test_help(self):
        """ Help returns a help page in Spanish """
        client = Client()
        help_url = reverse('judge:help')
        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')
        content = client.get(help_url, follow=True).content.decode('utf-8')
        self.assertIn("Presentación", content)

    def test_statistics(self):
        """ Statistics contains some text for staff and redirects standard and not logged users """
        client = Client()
        stats_url = reverse('judge:statistics_submissions')
        login_redirect_url = reverse('admin:login')
        login_redirect_stats_url = f'{login_redirect_url}?next={stats_url}'

        # Staff user
        create_superuser('0000', username='staff')
        client.login(username='staff', password='0000')
        content = client.get(stats_url, follow=True).content.decode('utf-8')
        self.assertIn("Número de envíos", content)
        self.assertIn("TLE", content)
        client.logout()

        # Standard user -> redirects to admin login
        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')
        response = client.get(stats_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_stats_url, 302)])
        client.logout()

        # Not logged user -> redirects to admin login
        response = client.get(stats_url, follow=True)
        self.assertEqual(response.redirect_chain,
                         [(login_redirect_stats_url, 302)])
