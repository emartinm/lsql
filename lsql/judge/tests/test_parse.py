# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the parse module
"""

import os
from zipfile import ZipFile

from django.test import TestCase
from django.core.exceptions import ValidationError

from judge.models import Collection, Problem, SelectProblem, DMLProblem, FunctionProblem, \
    ProcProblem, TriggerProblem, DiscriminantProblem


class ParseTest(TestCase):
    """Tests for module parse"""
    ZIP_FOLDER = 'zip_files'

    MANY_PROBLEMS_ZIP_NAME = 'problems.zip'

    NO_JSON = 'no_json.zip'
    NO_TYPE = 'no_type.zip'

    SELECT_OK = 'select_ok.zip'
    DML_OK = 'dml_ok.zip'
    FUNCTION_OK = 'function_ok.zip'
    PROC_OK = 'proc_ok.zip'
    TRIGGER_OK = 'trigger_ok.zip'
    DISCRIMINANT_OK = 'discriminant_ok.zip'

    SELECT_MISSING_FILES = 'select_missing_files.zip'
    SELECT_EMPTY_TITLE = 'select_empty_title.zip'
    SELECT_TEXT_DECODE = 'select_text_decode.zip'

    DML_MISSING_FILES = 'dml_missing_files.zip'
    DML_BAD_NUM_STMT = 'dml_bad_num_stmt.zip'
    DML_TEXT_DECODE = 'dml_text_decode.zip'

    FUNCTION_MISSING_FILES = 'function_missing_files.zip'
    FUNCTION_EMPTY_TITLE = 'function_empty_title.zip'
    FUNCTION_TEXT_DECODE = 'function_text_decode.zip'

    PROC_MISSING_FILES = 'proc_missing_files.zip'
    PROC_EMPTY_TITLE = 'proc_empty_title.zip'
    PROC_TEXT_DECODE = 'proc_text_decode.zip'

    TRIGGER_MISSING_FILES = 'trigger_missing_files.zip'
    TRIGGER_EMPTY_TITLE = 'trigger_empty_title.zip'
    TRIGGER_TEXT_DECODE = 'trigger_text_decode.zip'
    TRIGGER_BAD_INSERT = 'trigger_bad_insert.zip'

    DISCRIMINANT_MISSING_FILES = 'discriminant_missing_files.zip'
    DISCRIMINANT_BAD_STMT = 'discriminant_bad_stmt.zip'
    DISCRIMINANT_TEXT_DECODE = 'discriminant_text_decode.zip'

    def test_no_json(self):
        """Loading problem details form a ZIP without JSON file"""
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, self.ZIP_FOLDER, self.NO_JSON)

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
        zip_path = os.path.join(curr_path, self.ZIP_FOLDER, self.NO_TYPE)

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
        zip_select_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, self.ZIP_FOLDER, self.DML_OK)
        zip_function_path = os.path.join(curr_path, self.ZIP_FOLDER, self.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, self.ZIP_FOLDER, self.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, self.ZIP_FOLDER, self.TRIGGER_OK)

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
        zip_select_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_OK)
        zip_dml_path = os.path.join(curr_path, self.ZIP_FOLDER, self.DML_OK)
        zip_function_path = os.path.join(curr_path, self.ZIP_FOLDER, self.FUNCTION_OK)
        zip_proc_path = os.path.join(curr_path, self.ZIP_FOLDER, self.PROC_OK)
        zip_trigger_path = os.path.join(curr_path, self.ZIP_FOLDER, self.TRIGGER_OK)
        zip_discriminant_path = os.path.join(curr_path, self.ZIP_FOLDER, self.DISCRIMINANT_OK)

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

    def test_load_many_problems(self):
        """Test for loading a ZIP containing several problems"""
        curr_path = os.path.dirname(__file__)
        zip_path = os.path.join(curr_path, self.ZIP_FOLDER, self.MANY_PROBLEMS_ZIP_NAME)
        collection = Collection(name_md='Colección', position=8, description_md='Colección de pruebas',
                                author=None)
        collection.clean()
        collection.save()
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
        for filename in [self.SELECT_MISSING_FILES, self.SELECT_EMPTY_TITLE, self.SELECT_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, self.ZIP_FOLDER, filename)
            problem = SelectProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # DML problems
        for filename in [self.DML_MISSING_FILES, self.DML_BAD_NUM_STMT, self.DML_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, self.ZIP_FOLDER, filename)
            problem = DMLProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Function problems
        for filename in [self.FUNCTION_MISSING_FILES, self.FUNCTION_EMPTY_TITLE, self.FUNCTION_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, self.ZIP_FOLDER, filename)
            problem = FunctionProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Procedure problems
        for filename in [self.PROC_MISSING_FILES, self.PROC_EMPTY_TITLE, self.PROC_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, self.ZIP_FOLDER, filename)
            problem = ProcProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Trigger problems
        for filename in [self.TRIGGER_MISSING_FILES, self.TRIGGER_EMPTY_TITLE, self.TRIGGER_TEXT_DECODE,
                         self.TRIGGER_BAD_INSERT]:
            zip_path = os.path.join(curr_path, self.ZIP_FOLDER, filename)
            problem = TriggerProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)

        # Discriminant problems
        for filename in [self.DISCRIMINANT_MISSING_FILES, self.DISCRIMINANT_BAD_STMT,
                         self.DISCRIMINANT_TEXT_DECODE]:
            zip_path = os.path.join(curr_path, self.ZIP_FOLDER, filename)
            problem = DiscriminantProblem(zipfile=zip_path)
            self.assertRaises(ValidationError, problem.clean)
