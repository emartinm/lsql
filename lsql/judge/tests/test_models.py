# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for models
"""
import os

from django.core.exceptions import ValidationError
from django.test import TestCase
import django.contrib.auth

from judge.models import SelectProblem, Collection, Submission, Problem
from judge.types import VeredictCode


class ModelsTest(TestCase):
    """Tests for models"""
    ZIP_FOLDER = 'zip_files'
    CORRUPT_ZIP = 'broken_problems.zip'
    CORRUPT_SELECT_ZIP = 'broken_select.zip'
    CORRUPT_ZIP_INSIDE = 'broken_problems_inside.zip'

    def test_problem_collection_stats(self):
        """Methods that compute statistics in collections and problems"""
        collection = Collection(name_md='ABC', description_md='blablabla')
        collection.clean()
        collection.save()
        self.assertTrue('ABC' in str(collection))

        user_model = django.contrib.auth.get_user_model()

        create = 'CREATE TABLE mytable (dd DATE);'
        insert = "INSERT INTO mytable VALUES (TO_DATE('2020/01/31', 'yyyy/mm/dd'))"
        solution = 'SELECT * FROM mytable'
        problem1 = SelectProblem(title_md='Dates', text_md='Example with dates',
                                 create_sql=create, insert_sql=insert, collection=collection,
                                 solution=solution)
        problem2 = SelectProblem(title_md='Dates', text_md='Example with dates',
                                 create_sql=create, insert_sql=insert, collection=collection,
                                 solution=solution)
        problem3 = SelectProblem(title_md='Dates', text_md='Example with dates',
                                 create_sql=create, insert_sql=insert, collection=collection,
                                 solution=solution)
        user1 = user_model.objects.create_user(username='usuario1', email='algo@ucm.es', password='1234')
        user2 = user_model.objects.create_user(username='usuario2', email='algodistinto@ucm.es', password='1234')
        problem1.clean()
        problem1.save()
        problem2.clean()
        problem2.save()
        problem3.clean()
        problem3.save()
        user1.save()
        user2.save()

        sub1 = Submission(code='nada', veredict_code=VeredictCode.WA, user=user1, problem=problem1)
        sub2 = Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1)
        sub3 = Submission(code='nada', veredict_code=VeredictCode.TLE, user=user1, problem=problem1)
        sub4 = Submission(code='nada', veredict_code=VeredictCode.RE, user=user1, problem=problem1)
        sub5 = Submission(code='nada', veredict_code=VeredictCode.VE, user=user1, problem=problem1)
        sub6 = Submission(code='nada', veredict_code=VeredictCode.IE, user=user1, problem=problem1)
        self.assertTrue('WA' in str(sub1))
        self.assertTrue('AC' in str(sub2))

        for sub in [sub1, sub2, sub3, sub4, sub5, sub6]:
            sub.save()

        # Problem solved
        self.assertTrue(problem1.solved_by_user(user1))
        self.assertFalse(problem1.solved_by_user(user2))
        self.assertFalse(problem2.solved_by_user(user1))
        self.assertFalse(problem2.solved_by_user(user2))

        # Number of submissions
        self.assertEqual(problem1.num_submissions_by_user(user1), 6)
        self.assertEqual(problem1.num_submissions_by_user(user2), 0)
        self.assertEqual(problem2.num_submissions_by_user(user1), 0)
        self.assertEqual(problem2.num_submissions_by_user(user2), 0)

        # Problems in collection
        self.assertEqual(collection.problems().count(), 3)
        self.assertEqual(collection.num_problems(), 3)

        # Numbers of problems solved by a user
        self.assertEqual(collection.num_solved_by_user(user1), 1)
        self.assertEqual(collection.num_solved_by_user(user2), 0)

    def test_load_broken_zip(self):
        """Open corrupt ZIP files"""
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, self.ZIP_FOLDER, self.CORRUPT_ZIP)
        collection = Collection(name_md='Colección', position=8, description_md='Colección de pruebas',
                                author=None)
        collection.clean()
        collection.save()

        # Loading a broken ZIP file with several problems
        collection.zipfile = zip_path
        self.assertRaises(ValidationError, collection.clean)

        # Loading a broken ZIP file a select problem
        zip_path = os.path.join(curr_path, self.ZIP_FOLDER, self.CORRUPT_SELECT_ZIP)
        problem = SelectProblem(zipfile=zip_path)
        self.assertRaises(ValidationError, problem.clean)

        # Loading a correct ZIP file that contains a broken ZIP
        zip_path = os.path.join(curr_path, self.ZIP_FOLDER, self.CORRUPT_ZIP_INSIDE)
        collection.zipfile = zip_path
        self.assertRaises(ValidationError, collection.clean)

    def test_abstract_problem(self):
        """Abstract methods in a Problem raise exceptions"""
        collection = Collection()
        collection.save()
        problem = Problem(title_md='Dates', text_md='Example with dates',
                          create_sql='   ', insert_sql='    ', collection=collection)
        self.assertRaises(NotImplementedError, problem.template)
        self.assertRaises(NotImplementedError, problem.judge, '', None)
        self.assertRaises(NotImplementedError, problem.problem_type)

    def test_num_statements(self):
        """Incorrect number of statements must raise a ValidationError"""
        collection = Collection()
        collection.save()
        create = 'CREATE TABLE arg (n NUMBER);'
        insert = "INSERT INTO arg VALUES (88)"
        solution = 'SELECT * FROM arg'
        problem = SelectProblem(title_md='Test', text_md='Simple Table',
                                create_sql=create, insert_sql=insert, collection=collection,
                                min_stmt=5, max_stmt=2,  # Impossible
                                solution=solution)
        self.assertRaises(ValidationError, problem.clean)
