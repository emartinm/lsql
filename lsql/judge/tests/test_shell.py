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
    submissions_per_user, create_users_from_list, is_projection, is_where, is_aggregation, is_order, is_inner_join, \
    is_outer_join, is_group_by, is_set, is_having, is_nested, is_null, is_exists, is_like, keywords, apply_sql_checker
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

        for prob in Problem.objects.all():  # pylint: disable=E1133
            # pylint false positive E1133
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

class KeywordTest(TestCase):
    """ Test cases for labeling SQL expression with keywords """

    def test_is_projection(self):
        """ Tests for is_projection() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club", "SELECT * FROM Club JOIN Person WHERE 1 = 3 ORDER BY Club.ID",
                      "SELECT * FROM Club WHERE ID NOT IN (SELECT * FROM Person)",
                      ]
        test_true = ["SELECT ID FROM Club", "SELECT Name, ID FROM Club",
                     "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person", "SELECT COUNT(*) FROM Club",
                     "SELECT * FROM Club WHERE ID NOT IN (SELECT ID FROM Person)",
                     "SELECT ID FROM Club WHERE ID NOT IN (SELECT * FROM Person)",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees, avg_total_salary;"""
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_projection))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_projection))

    def test_is_where(self):
        """ Tests for is_where() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club", "SELECT * FROM Club JOIN Person ON ID1 = ID2 ORDER BY Club.ID",
                      "SELECT A, B, COUNT(*) FROM Club GROUP BY A, B",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID, Name FROM Club GROUP BY ID, Name HAVING Name = 'WHERE'",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees, avg_total_salary;"""
                      ]
        test_true = ["SELECT * FROM Club Where ID = 0",
                     "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person WHERE 1 = 4",
                     "SELECT * FROM Club WHERE ID NOT IN (SELECT ID FROM Person)",
                     "SELECT ID FROM Club WHERE ID NOT IN (SELECT * FROM Person)",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                                WHERE ID = 4
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees, avg_total_salary;"""
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_where))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_where))

    def test_is_order(self):
        """ Tests for is_order() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person WHERE 1 = 4",
                      "SELECT A, B, COUNT(*) FROM Club GROUP BY A, B",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID, Name FROM Club GROUP BY ID, Name HAVING Name = 'WHERE'",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees, avg_total_salary;"""
                      ]
        test_true = ["SELECT * FROM Club JOIN Person ON ID1 = ID2 ORDER BY Club.ID",
                     "SELECT * FROM Club JOIN Person ON ID1 = ID2 ORDER BY Club.ID ASC",
                     "SELECT * FROM Club RIGHT JOIN Person ON ID1 = ID2 ORDER BY Club.ID DESC",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                                WHERE ID = 4
                                                ORDER BY ID ASC
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees, avg_total_salary;"""
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_order))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_order))

    def test_is_inner_join(self):
        """ Tests for is_inner_join() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT OUTER JOIN ON A = B Person WHERE 1 = 4",
                      "SELECT * FROM Club RIGHT JOIN Person ON ID1 = ID2 ORDER BY Club.ID DESC",
                      "SELECT * FROM Club FULL OUTER JOIN Person ON ID1 = ID2 ORDER BY Club.ID DESC",
                      "SELECT A, B, COUNT(*) FROM Club GROUP BY A, B",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID, Name FROM Club GROUP BY ID, Name HAVING Name = 'WHERE'",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees LEFT JOIN avg_total_salary;"""
                      ]
        test_true = ["SELECT * FROM Club JOIN Person ON ID1 = ID2",
                     "SELECT * FROM Club INNER JOIN Person ON ID1 = ID2",
                     "SELECT * FROM Club JOIN Person USING (ID1, ID2)",
                     "SELECT * FROM Club INNER JOIN Person USING (ID1, ID2)",
                     "SELECT * FROM Club JOIN Person ON ID1 = ID2 ORDER BY Club.ID ASC",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                                WHERE ID = 4
                                                ORDER BY ID ASC
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees JOIN avg_total_salary USING A;"""
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_inner_join))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_inner_join))

    def test_is_outer_join(self):
        """ Tests for is_outer_join() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club INNER JOIN Person USING B WHERE 1 = 4",
                      "SELECT A, B, COUNT(*) FROM Club GROUP BY A, B",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID, Name FROM Club GROUP BY ID, Name HAVING Name = 'WHERE'",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees JOIN avg_total_salary ON A = B"""
                      ]
        test_true = ["SELECT * FROM Club LEFT JOIN Person ON ID1 = ID2",
                     "SELECT * FROM Club RIGHT JOIN Person ON ID1 = ID2",
                     "SELECT * FROM Club RIGHT OUTER JOIN Person ON ID1 = ID2",
                     "SELECT * FROM Club LEFT OUTER JOIN Person ON ID1 = ID2",
                     "SELECT * FROM Club FULL OUTER JOIN Person ON ID1 = ID2",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                                WHERE ID = 4
                                                ORDER BY ID ASC
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B"""
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_outer_join))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_outer_join))

    def test_is_aggregation(self):
        """ Tests for is_aggregation() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid,
                      "SELECT * FROM Club", "SELECT * FROM Club JOIN Person ON ID1 = ID2 ORDER BY Club.ID",
                      "SELECT * FROM Club Where ID = 0",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person WHERE 1 = 4",
                      "SELECT * FROM Club WHERE ID NOT IN (SELECT ID FROM Person)",
                      "SELECT ID FROM Club WHERE ID NOT IN (SELECT * FROM Person)",
                      "SELECT * FROM Club WHERE Name = 'AVG(Edad)'",
                      "SELECT Name AS 'SUM(Gol)' FROM Club",
                      """WITH avg_total_salary AS (
                                                 SELECT salary AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees, avg_total_salary;""",
        ]
        test_true = ["SELECT COUNT(*) FROM Club",
                     "SELECT A, B, COUNT(Distinct Name) FROM Club GROUP BY A, B",
                     "SELECT ID, AVG(Edad) FROM Club WHERE Name Like 'Aaron%'",
                     "SELECT SUM(Gol) FROM Club WHERE 3 > 6",
                     "SELECT suM(Gol) FROM Club WHERE 3 > 6",
                     "SELECT * FROM Club WHERE Name IN (SELECT MIN(Name) FROM Club)",
                     "SELECT * FROM Club WHERE NOT EXISTS (SELECT ID, MAX(Name) FROM Club)",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees, avg_total_salary;""",
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql,is_aggregation))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql,is_aggregation))

    def test_is_group_by(self):
        """ Tests for is_group_by() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees JOIN avg_total_salary ON A = B"""
                      ]
        test_true = ["SELECT A, B, COUNT(*) FROM Club GROUP BY A, B",
                     "SELECT ID, Name FROM Club GROUP BY ID, Name HAVING Name = 'WHERE'",
                     "SELECT ID FROM Club GROUP BY ID",
                     """WITH avg_total_salary AS (
                                                SELECT AVG(salary) AS average_company_salary
                                                FROM employees
                                                WHERE ID = 4
                                                GROUP BY P
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B;""",
                     "SELECT * FROM (SELECT * FROM C GROUP BY ID)"
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_group_by))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_group_by))

    def test_is_set(self):
        """ Tests for is_group_by() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID FROM Club GROUP BY ID",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees JOIN avg_total_salary ON A = B"""
                      ]
        test_true = ["(SELECT A, B, COUNT(*) FROM Club) UNION (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) INTERSECT (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) INTERSECT ALL (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) MINUS (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) MINUS ALL (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) EXCEPT (SELECT * FROM Me)",
                     "(SELECT A, B, COUNT(*) FROM Club) EXCEPT ALL (SELECT * FROM Me)",
                     """WITH avg_total_salary AS (
                                                (SELECT A, B, COUNT(*) FROM Club) EXCEPT (SELECT * FROM Me)
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B;""",
                     "SELECT * FROM ((SELECT * FROM C GROUP BY ID) UNION ALL (SELECT * FROM Me))"
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_set))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_set))

    def test_is_having(self):
        """ Tests for is_group_by() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID FROM Club GROUP BY ID",
                      """WITH avg_total_salary AS (
                                                 SELECT AVG(salary) AS average_company_salary
                                                 FROM employees
                                               )
                                               SELECT id, first_name, last_name, salary, department, 
                                                      average_company_salary,
                                                      salary - average_company_salary  AS salary_difference
                                               FROM employees JOIN avg_total_salary ON A = B""",
                      "(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)",
                      ]
        test_true = ["SELECT ID FROM Club GROUP BY ID HAVING COUNT(*) > 3",
                     "SELECT ID FROM Club WHERE ID > 66 GROUP BY ID HAVING SUM(P) > 3",
                     "SELECT ID FROM Club WHERE ID > 66 GROUP BY ID HAVING SUM(P) > 3 ORDER BY SUM(P)",
                     """WITH avg_total_salary AS (
                                                SELECT ID FROM Club WHERE ID > 66 GROUP BY ID HAVING SUM(P) = 3
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B;""",
                     "SELECT * FROM (SELECT * FROM C GROUP BY P HAVING MAX(A) = 0)"
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql,is_having))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql,is_having))

    def test_is_nested(self):
        """ Tests for is_nested() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID FROM Club GROUP BY ID",
                      "(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)",
                      ]
        test_true = ["SELECT ID, (SELECT MAX(ID) FROM Club) FROM Club",
                     "SELECT ID, Name FROM Club JOIN (SELECT A, B FROM Club) ON A = B",
                     "SELECT ID, Name FROM Club JOIN LEFT JOIN P ON A = B WHERE Age > ANY (SELECT Age FROM P)",
                     """SELECT ID, Name FROM Club JOIN LEFT JOIN P ON A = B GROUP BY ID, Name
                        HAVING SUM(A) > ALL (SELECT * FROM AG)""",
                     """WITH avg_total_salary AS (
                                                SELECT ID FROM Club WHERE ID > 66 GROUP BY ID HAVING SUM(P) = 3
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B;""",
                     "SELECT * FROM (SELECT * FROM C GROUP BY P HAVING MAX(A) = 0)",
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql,is_nested))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql,is_nested))

    def test_is_null(self):
        """ Tests for is_null() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID FROM Club GROUP BY ID",
                      "(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)",
                      ]
        test_true = ["SELECT ID FROM Club WHERE Name IS NOT NULL",
                     "SELECT A, COALESCE(B, 45) FROM Club",
                     "SELECT A, B FROM Club WHERE NVL(A, 3) = 3",
                     "SELECT A, B FROM Club WHERE NVL2(A, 3) = 3",
                     """SELECT ID, Name FROM Club JOIN LEFT JOIN P ON A = B GROUP BY ID, Name
                        HAVING SUM(A) IS NOT NULL""",
                     "SELECT ID, NULL FROM Club",
                     """WITH avg_total_salary AS (
                                                SELECT ID, NVL(B, 55) FROM Club WHERE ID > 66
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B""",
                     "SELECT * FROM (SELECT * FROM C GROUP BY P HAVING MAX(A) IS NOT NULL)",
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_null))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_null))

    def test_is_exists(self):
        """ Tests for is_null() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID FROM Club GROUP BY ID",
                      "(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)",
                      "SELECT ID FROM Club WHERE Name IS NOT NULL",
                      "SELECT A, COALESCE(B, 45) FROM Club",
                      ]
        test_true = ["SELECT A, NVL2(B, 3) FROM Club WHERE EXISTS (SELECT * FROM Club)",
                     "SELECT A, B FROM Club GROUP BY ID HAVING EXISTS (SELECT * FROM Club)",
                     """SELECT Nombre FROM Club C1 WHERE NOT EXISTS 
                          (SELECT * FROM Club C2 WHERE C2.Num_Socios > C1.Num_Socios)""",
                     """WITH avg_total_salary AS (
                                                SELECT ID, NVL(B, 55) FROM Club WHERE NOT EXISTS (SELECT * FROM Me) 
                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B""",
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql, is_exists))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql, is_exists))

    def test_is_like(self):
        """ Tests for is_null() """
        test_false = ["SELECT * FROM FROM",  # Syntactically invalid
                      "SELECT * FROM Club",
                      "SELECT Club.Name, Person.ID FROM Club JOIN Person ON A = B WHERE 1 = 4",
                      "SELECT Club.Name, Person.ID FROM Club LEFT JOIN Person USING B WHERE 1 = 4",
                      "SELECT COUNT(*) FROM Club",
                      "SELECT ID FROM Club GROUP BY ID",
                      "(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)",
                      "SELECT ID FROM Club WHERE Name IS NOT NULL",
                      "SELECT A, COALESCE(B, 45) FROM Club",
                      ]
        test_true = ["SELECT A, NVL2(B, 3) FROM Club WHERE Name LIKE 'Pe%'",
                     "SELECT A, B FROM Club GROUP BY ID HAVING Name LIKE '%AA_'",
                     "SELECT Nombre FROM Club C1 WHERE NOT EXISTS (SELECT * FROM Club C2 WHERE Name LIKE 'A%A')",
                     """WITH avg_total_salary AS (
                                                SELECT ID, NVL(B, 55) FROM Club WHERE Name Like 'My%'

                                              )
                                              SELECT id, first_name, last_name, salary, department, 
                                                     average_company_salary,
                                                     salary - average_company_salary  AS salary_difference
                                              FROM employees LEFT OUTER JOIN avg_total_salary ON A = B""",
                     ]
        for sql in test_false:
            self.assertFalse(apply_sql_checker(sql,is_like))
        for sql in test_true:
            self.assertTrue(apply_sql_checker(sql,is_like))

    def test_keywords(self):
        """ Test for generating keyword tags for a SQL query """
        self.assertEqual(keywords("(SELECT A, B, COUNT(*) FROM Club) UNION ALL (SELECT * FROM Me)"),
                         {"projection", "aggregation", "set"})
        self.assertEqual(keywords("SELECT Nombre FROM Club C1 WHERE NOT EXISTS "
                                  "(SELECT * FROM Club C2 WHERE C2.Num_Socios > C1.Num_Socios)"),
                         {"projection", "where", "nested", "exists"})
        self.assertEqual(keywords("""SELECT C.CIF, C.Nombre, NVL(AVG(Cantidad),0) AS PromedioFinanciaciones,
                                             COUNT(Cantidad) AS TotalFinanciaciones 
                                      FROM Financia F RIGHT JOIN Club C ON F.CIF_C = C.CIF 
                                      GROUP BY C.CIF, C.Nombre"""),
                         {"projection", "outer_join", "aggregation", "group_by", "null"})
        self.assertEqual(keywords("""select a.NIF as NIF, p.Nombre as NOMBRE,
                                             NVL(count(e.NIF), 0) as PARTIDOSARBITRADOS 
                                      from Arbitro a join Persona p on a.NIF = p.NIF left join Enfrenta e on a.NIF=e.NIF
                                      group by a.NIF, p.Nombre
                                      ORDER BY a.NIF DESC"""),
                         {"projection", "order", "inner_join", "outer_join", "aggregation", "group_by", "null"})
        self.assertEqual(keywords("SELECT * FROM FROM WHERE"), set())
        self.assertEqual(keywords("SELECT * FROM Club"), set())
        self.assertEqual(keywords("""SELECT P.NIF, P.Nombre
                                     FROM Jugador J JOIN Persona P ON J.NIF = P.NIF
                                     WHERE NOT EXISTS ((SELECT CIF -- Todos los patrocinadores
                                                        FROM Patrocinador
                                                        WHERE Rama = 'Deportes')
                                                       MINUS
                                                       (SELECT CIF -- Todos los patrocinadores del jugador
                                                        FROM Patrocina P
                                                        WHERE P.NIF = J.NIF));"""),
                         {"projection", "where", "inner_join", "set", "nested", "exists"})
        self.assertEqual(keywords("""SELECT Country
                                     FROM Club
                                     WHERE Club.Name LIKE 'A__%' 
                                     GROUP BY Country
                                     HAVING COUNT(*) > 3;"""),
                         {"projection", "where", "aggregation", "group_by", "having", "like"})
