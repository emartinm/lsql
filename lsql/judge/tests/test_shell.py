# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the shell module
"""
import datetime
import os
from tempfile import mkstemp
import csv

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from judge.types import VerdictCode
from judge.models import SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem, Collection, \
    Problem, Submission
from judge.shell import create_users_from_csv, adapt_db_result_to_list, rejudge, extended_submissions, \
    submissions_per_user, create_users_from_list
from judge.tests.test_common import create_select_problem, create_collection, create_user, create_dml_problem


class ShellTest(TestCase):
    """Tests for module parse"""
    FILE_FOLDER = 'csv_files'
    CSV_OK_TEST = 'test_ok.csv'
    CSV_BAD_FORMAT = ['csv_empty_document.csv', 'csv_empty_first.csv', 'csv_empty_name.csv', 'csv_empty_email.csv',
                      'csv_empty_last.csv', 'csv_non_ucm_email.csv']

    def test_create_users_from_list_bad(self):
        """ Invocations that must raise AssertionErrors """
        with self.assertRaises(AssertionError):
            create_users_from_list(dict_list=[], group=None, dry=True)

        with self.assertRaises(AssertionError):
            create_users_from_list(dict_list=[{'CORREO': '',
                                               'DOCUMENTO': '58962147S',
                                               'NOMBRE COMPLETO': 'Calabaza, Manuel'}],
                                   group='test', dry=True)

        with self.assertRaises(AssertionError):
            create_users_from_list(dict_list=[{'CORREO': '@ucm.es',
                                               'DOCUMENTO': '58962147S',
                                               'NOMBRE COMPLETO': 'Calabaza, Manuel'}],
                                   group='test', dry=True)

        with self.assertRaises(AssertionError):
            create_users_from_list(dict_list=[{'CORREO': 'pep@ucm.es',
                                               'DOCUMENTO': '',
                                               'NOMBRE COMPLETO': 'Calabaza, Manuel'}],
                                   group='test', dry=True)

        with self.assertRaises(AssertionError):
            create_users_from_list(dict_list=[{'CORREO': 'pep@ucm.es',
                                               'DOCUMENTO': '58962147S',
                                               'NOMBRE COMPLETO': 'Calabaza,'}],
                                   group='test', dry=True)

        with self.assertRaises(AssertionError):
            create_users_from_list(dict_list=[{'CORREO': 'pep@ucm.es',
                                               'DOCUMENTO': '58962147S',
                                               'NOMBRE COMPLETO': ',Manuel'}],
                                   group='test', dry=True)

    def test_valid_csv(self):
        """Valid CSV file with 3 users"""
        # Delete existing users and groups
        Group.objects.all().delete()
        get_user_model().objects.all().delete()

        group_name = 'Clase ABC curso X/Y'
        curr_path = os.path.dirname(__file__)
        path = os.path.join(curr_path, self.FILE_FOLDER, self.CSV_OK_TEST)

        # Invoking with dry=True does not create users or groups
        old_groups = list(Group.objects.all())
        old_users = list(get_user_model().objects.all())
        create_users_from_csv(path, group_name, dry=True)
        new_groups = list(Group.objects.all())
        new_users = list(get_user_model().objects.all())
        self.assertEqual(old_groups, new_groups)
        self.assertEqual(old_users, new_users)

        # Invoking with dry=False does create a group with the expected users
        create_users_from_csv(path, group_name, dry=False)

        # The new group has 3 members
        new_group = Group.objects.filter(name=group_name)[0]
        self.assertEqual(len(new_group.user_set.all()), 3)

        juan = get_user_model().objects.get(username='juan')
        self.assertTrue(juan.check_password('11111111X'))
        self.assertFalse(juan.check_password('11113111X'))
        self.assertEqual(juan.first_name, 'Juan')
        self.assertEqual(juan.last_name, '_')
        self.assertEqual(len(juan.groups.all()), 1)
        self.assertEqual(juan.groups.all()[0], new_group)

        eva = get_user_model().objects.get(username='eva')
        self.assertTrue(eva.check_password('22222222X'))
        self.assertFalse(eva.check_password('11113111X'))
        self.assertEqual(eva.first_name, 'EVA MARIA')
        self.assertEqual(eva.last_name, 'MARTIN KEPLER')
        self.assertEqual(len(eva.groups.all()), 1)
        self.assertEqual(eva.groups.all()[0], new_group)

        froilan = get_user_model().objects.get(username='froilan')
        self.assertTrue(froilan.check_password('33333333X'))
        self.assertFalse(froilan.check_password('11113111X'))
        self.assertEqual(froilan.first_name, 'JUAN FROILAN DE TODOS LOS SANTOS DE JESÚS')
        self.assertEqual(froilan.last_name, 'KUPU KUPI')
        self.assertEqual(len(froilan.groups.all()), 1)
        self.assertEqual(froilan.groups.all()[0], new_group)

    def test_bad_csv_format(self):
        """CSV files where some fields are empty"""
        curr_path = os.path.dirname(__file__)
        for filename in self.CSV_BAD_FORMAT:
            # Delete existing users and groups
            get_user_model().objects.all().delete()
            Group.objects.all().delete()
            path = os.path.join(curr_path, self.FILE_FOLDER, filename)
            with self.assertRaises(AssertionError):
                create_users_from_csv(path, f"Test-{filename}", dry=True)

    def test_adapt_db_expected_list(self):
        """Test for adapting dictionaries in initial_db and expected_result to unitary lists """
        collection = Collection(name_md='Colección', position=8, description_md='Colección de pruebas', author=None)
        collection.save()

        # Problems with dictionaries or already with [dict]
        problems = [
            SelectProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                          author=None, expected_result={}),
            DMLProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                       author=None, expected_result={}),
            FunctionProblem(title_html="titulo", text_html="enunciado", initial_db={},
                            collection=collection, author=None, expected_result={}),
            ProcProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                        author=None, expected_result={}),
            TriggerProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                           author=None, expected_result={}),
            SelectProblem(title_html="titulo", text_html="enunciado", initial_db=[{}], collection=collection,
                          author=None, expected_result=[{}]),  # already has the right representation
        ]

        for prob in problems:
            prob.save()

        adapt_db_result_to_list()
        for prob in Problem.objects.all().select_subclasses():
            self.assertIs(type(prob.initial_db), list)
            self.assertIs(type(prob.initial_db[0]), dict)
            self.assertIs(type(prob.expected_result), list)
            self.assertIs(type(prob.expected_result[0]), dict)

        for prob in Problem.objects.all():
            prob.delete()

        # Problems with wrong types in initial_db or expected_result
        wrong_problems = [
            SelectProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                          author=None, expected_result=3),
            DMLProblem(title_html="titulo", text_html="enunciado", initial_db=6, collection=collection,
                       author=None, expected_result={}),
            FunctionProblem(title_html="titulo", text_html="enunciado", initial_db=[],
                            collection=collection, author=None, expected_result={}),
            ProcProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                        author=None, expected_result=[3]),
            TriggerProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                           author=None, expected_result=[]),
            TriggerProblem(title_html="titulo", text_html="enunciado", initial_db={}, collection=collection,
                           author=None, expected_result=[{}, {}, False]),
        ]

        # Tries every wrong program individually (removing it after checking the exception)
        for prob in wrong_problems:
            prob.save()
            with self.assertRaises(TypeError):
                adapt_db_result_to_list()
            prob.delete()

    def test_rejudge(self):
        """ Test that rejudge correctly detects submission whose verdict changes """
        collection = create_collection("test collection")
        problem = create_select_problem(collection, "example")
        user = create_user(passwd='1111', username='user_Test')  # nosec B106
        subs = [
            Submission(code=problem.solution, verdict_code=VerdictCode.IE, user=user, problem=problem),  # IE->AC
            Submission(code='SELECT * FROM dual', verdict_code=VerdictCode.IE, user=user, problem=problem),  # IE->WA
            Submission(code='SELECT * FRO dual', verdict_code=VerdictCode.IE, user=user, problem=problem),  # IE->RE
        ]
        for sub in subs:
            sub.save()
            sub.creation_date = datetime.datetime(2020, 9, 15).astimezone()  # Sets an older date
            sub.save()

        file_desc, filename = mkstemp('_rejudge')
        os.close(file_desc)  # To avoid problems when removing the file in Windows
        rejudge(VerdictCode.IE, filename, tests=True)
        with open(filename, 'r', encoding='utf-8') as summary_file:
            summary = summary_file.read()
            self.assertIn('IE --> AC', summary)
            self.assertIn('IE --> WA', summary)
            self.assertIn('IE --> RE', summary)
            self.assertNotIn('IE --> IE', summary)
        os.remove(filename)

    def test_submission_info_csv(self):
        """ Test the CSV with extended submission information and the aggregated information """
        collection1 = create_collection("test collection1")
        collection2 = create_collection("test collection2")
        problem1 = create_select_problem(collection1, "Problem1")
        problem2 = create_dml_problem(collection2, "Problem2")
        user1 = create_user(passwd='1111', username='user1', email='user1@ucm.es')  # nosec B106
        user2 = create_user(passwd='1111', username='user2', email='user2@ucm.es')  # nosec B106
        sub1 = Submission(code='', verdict_code=VerdictCode.WA, user=user1, problem=problem1)
        sub2 = Submission(code='', verdict_code=VerdictCode.RE, user=user2, problem=problem1)
        sub3 = Submission(code='', verdict_code=VerdictCode.AC, user=user1, problem=problem2)
        subs = [sub1, sub2, sub3]
        for sub in subs:
            sub.save()

        file_desc, filename = mkstemp('_rejudge.csv')
        os.close(file_desc)  # To avoid problems when removing the file in Windows

        # Test extended
        extended_submissions(filename)
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 3)
            #####
            # Sometimes this test fails (nondeterministically) in GitHub Actions,
            # never locally. Temporary printing the rows from the CSV file to
            # help finding the bug
            print(rows)
            #####
            # Check submission information in the CSV
            for i, row in enumerate(rows):
                self.assertEqual(row['verdict'], subs[i].verdict_code)
                self.assertEqual(row['user'], subs[i].user.email)
                self.assertEqual(row['problem_name'], subs[i].problem.title_html)
                self.assertEqual(row['collection_name'], subs[i].problem.collection.name_html)
                self.assertEqual(row['problem_type'], str(subs[i].problem.problem_type()))

        submissions_per_user(filename)
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            # user1
            self.assertEqual(rows[0]['username'], 'user1@ucm.es')
            self.assertEqual(rows[0]['total_envios'], '2')
            self.assertEqual(rows[0]['envios_AC'], '1')
            self.assertEqual(rows[0]['envios_RE'], '0')
            self.assertEqual(rows[0]['envios_WA'], '1')
            self.assertEqual(rows[0]['problemas_intentados'], '2')
            self.assertEqual(rows[0]['ProblemType.SELECT'], '1')
            self.assertEqual(rows[0]['ProblemType.DML'], '1')
            self.assertEqual(rows[0]['ProblemType.PROC'], '0')
            # user2
            self.assertEqual(rows[1]['username'], 'user2@ucm.es')
            self.assertEqual(rows[1]['total_envios'], '1')
            self.assertEqual(rows[1]['envios_AC'], '0')
            self.assertEqual(rows[1]['envios_RE'], '1')
            self.assertEqual(rows[1]['envios_WA'], '0')
            self.assertEqual(rows[1]['problemas_intentados'], '1')
            self.assertEqual(rows[1]['ProblemType.SELECT'], '1')
            self.assertEqual(rows[1]['ProblemType.DML'], '0')
            self.assertEqual(rows[1]['ProblemType.PROC'], '0')
        os.remove(filename)
