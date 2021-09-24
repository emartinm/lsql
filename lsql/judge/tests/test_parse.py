# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the parse module
"""

import os
from zipfile import ZipFile

from django.test import TestCase
from django.core.exceptions import ValidationError

from judge.models import Problem, SelectProblem, DMLProblem, FunctionProblem, \
    ProcProblem, TriggerProblem, DiscriminantProblem
from judge.parse import get_language_from_json
from judge.exceptions import ZipFileParsingException
from judge.parse import get_problem_type_from_zip
from judge.tests.test_common import create_collection, TestPaths


class ParseTest(TestCase):
    """Tests for module parse"""

    def test_no_json(self):
        """Loading problem details form a ZIP without JSON file"""
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.NO_JSON)

        select_problem = SelectProblem(zipfile=zip_path)
        dml_problem = DMLProblem(zipfile=zip_path)
        function_problem = FunctionProblem(zipfile=zip_path)
        proc_problem = ProcProblem(zipfile=zip_path)
        trigger_problem = TriggerProblem(zipfile=zip_path)
        discriminant_problem = DiscriminantProblem(zipfile=zip_path)

        for problem in [select_problem, dml_problem, function_problem, proc_problem, trigger_problem,
                        discriminant_problem]:
            self.assertRaises(ValidationError, problem.clean)

    def test_no_type(self):
        """Loading problem details form a ZIP with a JSON file without type field"""
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.NO_TYPE)

        select_problem = SelectProblem(zipfile=zip_path)
        dml_problem = DMLProblem(zipfile=zip_path)
        function_problem = FunctionProblem(zipfile=zip_path)
        proc_problem = ProcProblem(zipfile=zip_path)
        trigger_problem = TriggerProblem(zipfile=zip_path)
        discriminant_problem = DiscriminantProblem(zipfile=zip_path)

        for problem in [select_problem, dml_problem, function_problem, proc_problem, trigger_problem,
                        discriminant_problem]:
            self.assertRaises(ValidationError, problem.clean)

    def test_zip_other_type(self):
        """Loading a problem data from a ZIP of a different type must raise a ValidationError"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.DML_OK)
        zip_function_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.TRIGGER_OK)

        select_problem = SelectProblem(zipfile=zip_dml_path)
        dml_problem = DMLProblem(zipfile=zip_function_path)
        function_problem = FunctionProblem(zipfile=zip_proc_path)
        proc_problem = ProcProblem(zipfile=zip_trigger_path)
        trigger_problem = TriggerProblem(zipfile=zip_select_path)
        discriminant_problem = TriggerProblem(zipfile=zip_select_path)

        for problem in [select_problem, dml_problem, function_problem, proc_problem, trigger_problem,
                        discriminant_problem]:
            self.assertRaises(ValidationError, problem.clean)

    def test_individual_zip(self):
        """Load problem data from valid ZIP"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.DML_OK)
        zip_function_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.TRIGGER_OK)
        zip_discriminant_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.DISCRIMINANT_OK)

        select_problem = SelectProblem(zipfile=zip_select_path)
        dml_problem = DMLProblem(zipfile=zip_dml_path)
        function_problem = FunctionProblem(zipfile=zip_function_path)
        proc_problem = ProcProblem(zipfile=zip_proc_path)
        trigger_problem = TriggerProblem(zipfile=zip_trigger_path)
        discriminant_problem = DiscriminantProblem(zipfile=zip_discriminant_path)

        for problem in [select_problem, dml_problem, function_problem, proc_problem, trigger_problem,
                        discriminant_problem]:
            self.assertFalse(problem.text_md)
            problem.clean()
            self.assertTrue(problem.text_md)
            self.assertTrue('.html' in problem.template())
            self.assertTrue(str(problem))
            self.assertEqual(problem.language, 'es')

    def test_load_many_problems(self):
        """ Test for loading a ZIP containing several problems """
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.MANY_PROBLEMS_ZIP_NAME)
        collection = create_collection(name='Collection')
        collection.zipfile = zip_path
        collection.clean()
        collection.save()

        # The new collection contains as many problems as files in the ZIP file
        with ZipFile(zip_path) as zfile:
            files_in_zip = len(zfile.namelist())
        self.assertEqual(Problem.objects.filter(collection=collection).count(), files_in_zip)

    def test_zip_errors(self):
        """ValidationError when loading ZIP in all problem types"""
        curr_path = os.path.dirname(__file__)

        # Select problems
        for filename in [TestPaths.SELECT_MISSING_FILES, TestPaths.SELECT_EMPTY_TITLE, TestPaths.SELECT_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, filename)
            problem = SelectProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # DML problems
        for filename in [TestPaths.DML_MISSING_FILES, TestPaths.DML_BAD_NUM_STMT, TestPaths.DML_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, filename)
            problem = DMLProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Function problems
        for filename in [TestPaths.FUNCTION_MISSING_FILES, TestPaths.FUNCTION_EMPTY_TITLE,
                         TestPaths.FUNCTION_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, filename)
            problem = FunctionProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Procedure problems
        for filename in [TestPaths.PROC_MISSING_FILES, TestPaths.PROC_EMPTY_TITLE, TestPaths.PROC_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, filename)
            problem = ProcProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Trigger problems
        for filename in [TestPaths.TRIGGER_MISSING_FILES, TestPaths.TRIGGER_EMPTY_TITLE, TestPaths.TRIGGER_TEXT_DECODE,
                         TestPaths.TRIGGER_BAD_INSERT]:
            zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, filename)
            problem = TriggerProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Discriminant problems
        for filename in [TestPaths.DISCRIMINANT_MISSING_FILES, TestPaths.DISCRIMINANT_BAD_STMT,
                         TestPaths.DISCRIMINANT_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, filename)
            problem = DiscriminantProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

    def test_language_json(self):
        """ Tests that language is correctly extracted from a problem JSON and unsupported languages raise
            ZipFileParsingException
        """
        self.assertEqual(get_language_from_json({'language': 'es'}), 'es')
        self.assertEqual(get_language_from_json({'language': 'en'}), 'en')
        with self.assertRaises(ZipFileParsingException):
            get_language_from_json({'language': 'ru'})

    def test_bad_json(self):
        """ Errors when decoding JSON or missing type """
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.JSON_DECODE_ERROR)
        problem = SelectProblem(zipfile=zip_path)
        with self.assertRaises(ValidationError) as ctxt:
            problem.clean()
        self.assertIn('Error when opening problem.json: Expecting value', str(ctxt.exception))

        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.NO_TYPE)
        self.assertIsNone(get_problem_type_from_zip(zip_path))

        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.WRONG_TYPE)
        SelectProblem(zipfile=zip_path)
        with self.assertRaises(ZipFileParsingException) as ctxt:
            get_problem_type_from_zip(zip_path)
        self.assertIn('Problem type is not defined in', str(ctxt.exception))

    def test_select_large(self):
        """ Test that a problem with many INSERT is loaded successfully """
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, TestPaths.ZIP_FOLDER, TestPaths.SELECT_LARGE)
        problem = SelectProblem(zipfile=zip_path)
        problem.clean()
        self.assertEqual(len(problem.expected_result), 1)
        self.assertEqual(len(problem.expected_result[0]['rows']), 895)
