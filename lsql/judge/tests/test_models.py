# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for models
"""
import os

from django.core.exceptions import ValidationError
from django.test import TestCase
import django.contrib.auth

from bs4 import BeautifulSoup
from judge.oracle_driver import OracleExecutor
from judge.models import SelectProblem, Collection, Submission, Problem
from judge.types import VeredictCode


class ModelsTest(TestCase):
    """Tests for models"""
    ZIP_FOLDER = 'zip_files'
    CORRUPT_ZIP = 'broken_problems.zip'
    CORRUPT_SELECT_ZIP = 'broken_select.zip'
    CORRUPT_ZIP_INSIDE = 'broken_problems_inside.zip'
    SELECT_MULTIPLE_DB_OK = 'select_multiple_db_ok.zip'

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

    def test_judge_multiple_db(self):
        """Test multiple db select problems"""
        curr_path = os.path.dirname(__file__)
        zip_select_multiple_db_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_MULTIPLE_DB_OK)
        select_multiple_db_problem = SelectProblem(zipfile=zip_select_multiple_db_path)

        select_multiple_db_problem.clean()

        self.assertEqual(len(select_multiple_db_problem.insert_sql_list()), 3)

        collection = Collection(name_md='ABC', description_md='blablabla')
        collection.clean()
        collection.save()
        self.assertTrue('ABC' in str(collection))

        create = '''CREATE TABLE Club(
                    CIF CHAR(9) PRIMARY KEY, -- No puede ser NULL
                    Nombre VARCHAR2(40) NOT NULL,
                    Sede VARCHAR2(30) NOT NULL,
                    Num_Socios NUMBER(10,0) NOT NULL,
                    CONSTRAINT NumSociosPositivos CHECK (Num_Socios >= 0)
                    );
                    CREATE TABLE Persona(
                    NIF CHAR(9) PRIMARY KEY,
                    Nombre VARCHAR2(20) NOT NULL
                    );'''
        insert = '''INSERT INTO Club VALUES ('11111111X', 'Madrid', 'A', 70000);

                    -- @new data base@

                    INSERT INTO Club VALUES ('11111111X', 'Madrid', 'A', 70000);
                    INSERT INTO Club VALUES ('11111112X', 'Futbol Club Barcelona', 'A', 80000);
                    INSERT INTO Club VALUES ('11111113X', 'Paris Saint-Germain Football Club', 'C', 1000);
                    INSERT INTO Persona VALUES ('00000001X', 'Peter Johnoson');
                    
                    -- @new data base@

                    INSERT INTO Club VALUES ('11111111X', 'Madrid', 'A', 70000);
                    INSERT INTO Club VALUES ('11111112X', 'Madrid', 'B', 80000);
                    INSERT INTO Club VALUES ('11111114X', 'Futbol Club Barcelona', 'B', 80000);
                    INSERT INTO Club VALUES ('11111115X', 'Paris Saint-Germain Football Club', 'C', 1000);
                    INSERT INTO Persona VALUES ('00000001X', 'Peter Johnoson');'''
        solution = "SELECT Sede, Nombre FROM Club WHERE CIF = '11111111X' and Nombre ='Madrid';"
        oracle = OracleExecutor.get()
        problem = SelectProblem(title_md='Test Multiple db Select', text_md='bla',
                            create_sql=create, insert_sql=insert, collection=collection,
                            author=None, check_order=False, solution=solution)
        problem.clean()
        problem.save()
        self.assertEqual(problem.judge(solution, oracle)[0], VeredictCode.AC)
        self.assertEqual(problem.judge("SELECT Sede, Nombre FROM Club WHERE Nombre ='Madrid';", oracle)[0],
                                       VeredictCode.WA)
        self.assertEqual(problem.judge("SELECT Sede, Nombre FROM Club;", oracle)[0], VeredictCode.WA)

        html = problem.judge("SELECT Sede, Nombre FROM Club WHERE CIF = '11111111X' and Nombre ='Madrid';", oracle)[1]
        soup = BeautifulSoup(html, 'html.parser')
        # Dont show db if code is correct
        self.assertIsNone(soup.find(id="bd"))

        html = problem.judge("SELECT Sede, Nombre FROM Club WHERE CIF = '11111117X';", oracle)[1]
        soup = BeautifulSoup(html, 'html.parser')
        # Dont show db if code is wrong in the first db
        self.assertIsNone(soup.find(id="bd"))

        html = problem.judge("SELECT Sede, Nombre FROM Club;", oracle)[1]
        soup = BeautifulSoup(html, 'html.parser')
        # Show second db if code is correct in the first db but not in the second db
        self.assertEqual(soup.find(id="bd").find('p').find('strong').string,
                        "Base de datos utilizada para la ejecución de tu código SQL:")
        self.assertEqual(soup.find(id="bd").find_all('thead')[0].find_all('th')[0].string,"CIF")
        self.assertEqual(soup.find(id="bd").find_all('thead')[0].find_all('th')[1].string,"NOMBRE")
        self.assertEqual(len(soup.find(id="bd").find_all('thead')),2)
        self.assertEqual(soup.find(id="bd").find_all('thead')[1].find_all('th')[0].string,"NIF")
        self.assertEqual(soup.find(id="bd").find_all('tbody')[0].find_all('tr')[1].find_all('td')[0].string,"11111112X")
        self.assertEqual(soup.find(id="bd").find_all('tbody')[0].find_all('tr')[1].find_all('td')[2].string,"A")
        self.assertEqual(len(soup.find(id="bd").find_all('tbody')[0].find_all('tr')),3)

        html = problem.judge("SELECT Sede, Nombre FROM Club WHERE Nombre ='Madrid';", oracle)[1]
        soup = BeautifulSoup(html, 'html.parser')
        # Show third db if code is correct in the first and second dbs but not in the third db
        self.assertEqual(soup.find(id="bd").find('p').find('strong').string,
                        "Base de datos utilizada para la ejecución de tu código SQL:")
        self.assertEqual(soup.find(id="bd").find_all('thead')[0].find_all('th')[0].string,"CIF")
        self.assertEqual(soup.find(id="bd").find_all('thead')[0].find_all('th')[1].string,"NOMBRE")
        self.assertEqual(soup.find(id="bd").find_all('tbody')[0].find_all('tr')[1].find_all('td')[0].string,"11111112X")
        self.assertEqual(soup.find(id="bd").find_all('tbody')[0].find_all('tr')[1].find_all('td')[2].string,"B")
        self.assertEqual(len(soup.find(id="bd").find_all('tbody')[0].find_all('tr')),4)


    def test_podium(self):
        """Test the correct performance of the podium"""
        collection = Collection(name_md='ABC', description_md='blablabla')
        collection.clean()
        collection.save()
        self.assertIn('ABC', str(collection))

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
        user1 = user_model.objects.create_user(username='usuario1', email='algo@ucm.es', password='1234')
        user2 = user_model.objects.create_user(username='usuario2', email='algodistinto@ucm.es', password='1234')
        user3 = user_model.objects.create_user(username='usuario3', email='algo2@ucm.es', password='1234')
        user4 = user_model.objects.create_user(username='usuario4', email='algo3@ucm.es', password='1234')

        problem1.clean()
        problem1.save()
        problem2.clean()
        problem2.save()
        user1.save()
        user2.save()
        user3.save()

        self.assertIsNone(problem1.solved_first())
        self.assertIsNone(problem1.solved_second())
        self.assertIsNone(problem1.solved_third())

        sub1 = Submission(code='nada', veredict_code=VeredictCode.WA, user=user1, problem=problem1)
        sub2 = Submission(code='nada', veredict_code=VeredictCode.IE, user=user1, problem=problem1)
        sub3 = Submission(code='nada', veredict_code=VeredictCode.TLE, user=user1, problem=problem1)
        sub4 = Submission(code='nada', veredict_code=VeredictCode.RE, user=user1, problem=problem1)
        sub5 = Submission(code='nada', veredict_code=VeredictCode.VE, user=user1, problem=problem1)

        for sub in [sub1, sub2, sub3, sub4, sub5]:
            sub.save()

        self.assertIsNone(problem1.solved_first())
        self.assertIsNone(problem1.solved_second())
        self.assertIsNone(problem1.solved_third())

        Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1).save()

        self.assertEqual(problem1.solved_first(), user1)
        self.assertIsNone(problem1.solved_second())
        self.assertIsNone(problem1.solved_third())

        Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1).save()
        Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1).save()

        self.assertEqual(problem1.solved_first(), user1)
        self.assertIsNone(problem1.solved_second())
        self.assertIsNone(problem1.solved_third())

        Submission(code='nada', veredict_code=VeredictCode.AC, user=user2, problem=problem1).save()

        self.assertEqual(problem1.solved_first(), user1)
        self.assertEqual(problem1.solved_second(), user2)
        self.assertIsNone(problem1.solved_third())

        Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1).save()
        Submission(code='nada', veredict_code=VeredictCode.AC, user=user3, problem=problem1).save()

        self.assertEqual(problem1.solved_first(), user1)
        self.assertEqual(problem1.solved_second(), user2)
        self.assertEqual(problem1.solved_third(), user3)

        Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1).save()
        Submission(code='nada', veredict_code=VeredictCode.AC, user=user1, problem=problem1).save()
        Submission(code='nada', veredict_code=VeredictCode.AC, user=user4, problem=problem1).save()

        self.assertEqual(problem1.solved_first(), user1)
        self.assertEqual(problem1.solved_second(), user2)
        self.assertEqual(problem1.solved_third(), user3)

        self.assertIsNone(problem2.solved_first())
        self.assertIsNone(problem2.solved_second())
        self.assertIsNone(problem2.solved_third())

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
