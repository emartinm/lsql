# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Parse problem and set of collections from a ZIP file
"""
from zipfile import ZipFile
import json

from .exceptions import ZipFileParsingException


__MAX_INT = 2 ** 31
__MIN_INT = -(2 ** 31)
__JSON_NAME = 'problem.json'
__SELECT_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md'}
__DML_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md'}
__FUNCTION_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__PROC_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__TRIGGER_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__DISCRIMINANT_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'text.md',
                                'incorrect_query.sql', 'correct_query.sql'}


def extract_json(file, problem_type):
    """
    :param problem_type: Problem type that should appear in the JSON file
    :param file: ZIP file
    :return: dict with the JSON file inside the ZIP
    """
    with ZipFile(file) as zfile:
        if __JSON_NAME not in zfile.namelist():
            raise ZipFileParsingException('Falta el fichero {}'.format(__JSON_NAME))

        with zfile.open(__JSON_NAME, 'r') as jsonfile:
            problem_json = json.load(jsonfile)

        json_problem_type = problem_json.get('type', None)
        if json_problem_type is None:
            raise ZipFileParsingException(f'Missing field "type" in file {__JSON_NAME}')
        if json_problem_type != problem_type:
            raise ZipFileParsingException(f'Invalid "type" field in {__JSON_NAME}: '
                                          f'expected {problem_type} but {json_problem_type} obtained')
    return problem_json


def load_select_problem(problem, file) -> None:
    """
    Load the problem information from a ZIP file and updates the attributes of 'problem'
    :param problem: SelectProblem to update
    :param file: ZipFile previoulsy opened and with a JSON File
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Checking file existence'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __SELECT_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    f'ZIP file must contain the following files: {__SELECT_PROBLEM_FILES}')

            state = 'Reading JSON file'
            problem.title_md = problem_json.get('title', '')
            problem.min_stmt = int(problem_json['min_stmt'])
            problem.max_stmt = int(problem_json['max_stmt'])
            problem.position = int(problem_json['position'])
            problem.check_order = bool(problem_json.get('check_order'))  # None will be converted to False
            if (not problem.title_md or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                    problem.min_stmt > problem.max_stmt):
                raise ZipFileParsingException('Invalid value in JSON file: "title", "min_stmt" or "max_stmt"')

            state = 'Reading text.md file'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode(encoding='utf-8')

            state = 'Reading create.sql file'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode(encoding='utf-8')
                problem.create_sql = create_str

            state = 'Reading insert.sql file'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode(encoding='utf-8')
                problem.insert_sql = insert_str

            state = 'Reading solution.sql file'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode(encoding='utf-8')
    except ZipFileParsingException:
        raise
    except Exception as excp:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(excp), excp)) from excp


def load_dml_problem(problem, file):
    """
    Load the problem information from a ZIP file and updates the attributes of 'problem'
    :param problem: DMLProblem to update
    :param file: ZipFile previoulsy opened and with a JSON File
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Checking file existence'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __DML_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    f'ZIP file must contain the following files: {__DML_PROBLEM_FILES}')

            state = 'Reading JSON file'
            problem.title_md = problem_json.get('title', '')
            problem.min_stmt = int(problem_json['min_stmt'])
            problem.max_stmt = int(problem_json['max_stmt'])
            problem.position = int(problem_json['position'])
            if (not problem.title_md or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                    problem.min_stmt > problem.max_stmt):
                raise ZipFileParsingException('Invalid value in JSON file: "title", "min_stmt" or "max_stmt"')

            state = 'Reading text.md file'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode(encoding='utf-8')

            state = 'Reading create.sql file'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode(encoding='utf-8')
                problem.create_sql = create_str

            state = 'Reading insert.sql file'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode(encoding='utf-8')
                problem.insert_sql = insert_str

            state = 'Reading solution.sql file'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode(encoding='utf-8')
    except ZipFileParsingException:
        raise
    except Exception as excp:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(excp), excp)) from excp


def load_function_problem(problem, file):
    """
    Load the problem information from a ZIP file and updates the attributes of 'problem'
    :param problem: DMLProblem to update
    :param file: ZipFile previoulsy opened and with a JSON File
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Checking file existence'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    f'ZIP file must contain the following files: {__FUNCTION_PROBLEM_FILES}')

            state = 'Reading JSON file'
            problem.title_md = problem_json.get('title', '')
            problem.position = int(problem_json['position'])
            if not problem.title_md:
                raise ZipFileParsingException('Invalid value in JSON file: "title"')

            state = 'Reading text.md file'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode(encoding='utf-8')

            state = 'Reading create.sql file'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode(encoding='utf-8')
                problem.create_sql = create_str

            state = 'Reading insert.sql file'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode(encoding='utf-8')
                problem.insert_sql = insert_str

            state = 'Reading solution.sql file'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode(encoding='utf-8')

            state = 'Leyendo fichero tests.sql'
            with zfile.open('tests.sql', 'r') as tests_file:
                problem.calls = tests_file.read().decode(encoding='utf-8')
    except ZipFileParsingException:
        raise
    except Exception as excp:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(excp), excp)) from None


def load_proc_problem(problem, file):
    """
    Load the problem information from a ZIP file and updates the attributes of 'problem'
    :param problem: DMLProblem to update
    :param file: ZipFile previoulsy opened and with a JSON File
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Checking file existence'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __PROC_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    f'ZIP file must contain the following files: {__PROC_PROBLEM_FILES}')

            state = 'Reading JSON file'
            problem.title_md = problem_json.get('title', '')
            problem.position = int(problem_json['position'])
            if not problem.title_md:
                raise ZipFileParsingException('Invalid value in JSON file: "title"')

            state = 'Reading text.md file'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode(encoding='utf-8')

            state = 'Reading create.sql file'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode(encoding='utf-8')
                problem.create_sql = create_str

            state = 'Reading insert.sql file'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode(encoding='utf-8')
                problem.insert_sql = insert_str

            state = 'Reading solution.sql file'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode(encoding='utf-8')

            state = 'Leyendo fichero tests.sql'
            with zfile.open('tests.sql', 'r') as tests_file:
                problem.proc_call = tests_file.read().decode(encoding='utf-8').strip()
    except ZipFileParsingException:
        raise
    except Exception as excp:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(excp), excp)) from excp


def load_trigger_problem(problem, file):
    """
        Load the problem information from a ZIP file and updates the attributes of 'problem'
        :param problem: DMLProblem to update
        :param file: ZipFile previoulsy opened and with a JSON File
        :return: None or raise ZipFileParsingException if there is any problem
        """
    state = 'Checking file existence'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __TRIGGER_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    f'ZIP file must contain the following files: {__TRIGGER_PROBLEM_FILES}')

            state = 'Reading JSON file'
            problem.title_md = problem_json.get('title', '')
            problem.position = int(problem_json['position'])
            if not problem.title_md:
                raise ZipFileParsingException('Invalid values in JSON file: "title"')

            state = 'Reading text.md file'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode(encoding='utf-8')

            state = 'Reading create.sql file'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode(encoding='utf-8')
                problem.create_sql = create_str

            state = 'Reading insert.sql file'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode(encoding='utf-8')
                problem.insert_sql = insert_str

            state = 'Reading solution.sql file'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode(encoding='utf-8')

            state = 'Leyendo fichero tests.sql'
            with zfile.open('tests.sql', 'r') as tests_file:
                problem.tests = tests_file.read().decode(encoding='utf-8').strip()
    except ZipFileParsingException:
        raise
    except Exception as excp:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(excp), excp)) from excp


def load_discriminant_problem(problem, file):
    """
        Load the problem information from a ZIP file and updates the attributes of 'problem'
        :param problem: DiscriminantProblem to update
        :param file: ZipFile previoulsy opened and with a JSON File
        :return: None or raise ZipFileParsingException if there is any problem
        """
    state = 'Checking file existence'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __DISCRIMINANT_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    f'ZIP file must contain the following files: {__DISCRIMINANT_PROBLEM_FILES}')

            state = 'Reading JSON file'
            problem.title_md = problem_json.get('title', '')
            problem.min_stmt = int(problem_json['min_stmt'])
            problem.max_stmt = int(problem_json['max_stmt'])
            problem.position = int(problem_json['position'])
            problem.check_order = bool(problem_json.get('check_order'))  # None will be converted to False
            if (not problem.title_md or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                    problem.min_stmt > problem.max_stmt):
                raise ZipFileParsingException('Invalid value in JSON file: "title", "min_stmt" or "max_stmt"')

            state = 'Reading text.md file'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode(encoding='utf-8')

            state = 'Reading create.sql file'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode(encoding='utf-8')
                problem.create_sql = create_str

            state = 'Reading insert.sql file'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode(encoding='utf-8')
                problem.insert_sql = insert_str

            state = 'Reading incorrect_query.sql file'
            with zfile.open('incorrect_query.sql', 'r') as incorrect_file:
                problem.incorrect_query = incorrect_file.read().decode(encoding='utf-8')

            state = 'Reading correct_query.sql file'
            with zfile.open('correct_query.sql', 'r') as correct_file:
                problem.correct_query = correct_file.read().decode(encoding='utf-8')
    except ZipFileParsingException:
        raise
    except Exception as excp:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(excp), excp)) from excp
