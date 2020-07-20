# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Parse problem and set of collections from a ZIP file
"""
from zipfile import ZipFile
import json

from .exceptions import ZipFileParsingException
import judge.models

__MAX_INT = 2 ** 31
__MIN_INT = -(2 ** 31)
__JSON_NAME = 'problem.json'
__SELECT_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md'}
__DML_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md'}
__FUNCTION_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__PROC_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__TRIGGER_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}


def parse_many_problems(file, collection):
    problems = list()
    try:
        with ZipFile(file) as zf:
            for filename in zf.infolist():
                curr_file = zf.open(filename)
                problem = load_problem_from_file(curr_file)
                problem.collection = collection
                problem.author = collection.author
                problems.append(problem)
    except ZipFileParsingException as e:
        raise ZipFileParsingException('{}: {}'.format(filename.filename, e))
    except Exception as e:
        raise ZipFileParsingException("{}: {}".format(type(e), e))
    return problems


def load_problem_from_file(file):
    """Tries to load all the types of problem from file, in order"""
    problem_types = [(judge.models.SelectProblem, load_select_problem),
                     (judge.models.DMLProblem, load_dml_problem),
                     (judge.models.FunctionProblem, load_function_problem),
                     (judge.models.ProcProblem, load_proc_problem),
                     (judge.models.TriggerProblem, load_trigger_problem)
                     ]

    for pclass, load_fun in problem_types:
        problem = pclass()
        try:
            load_fun(problem, file)
            return problem
        except ZipFileParsingException:
            # It is not the type, try next one
            pass
    return None


def extract_json(file, problem_type):
    """
    :param problem_type: Problem type that should appear in the JSON file
    :param file: ZIP file
    :return: dict with the JSON file inside the ZIP
    """
    try:
        with ZipFile(file) as zfile:
            if __JSON_NAME not in zfile.namelist():
                raise ZipFileParsingException('Falta el fichero {}'.format(__JSON_NAME))

            with zfile.open(__JSON_NAME, 'r') as jsonfile:
                problem_json = json.load(jsonfile)

                json_problem_type = problem_json.get('type', None)
                if json_problem_type is None:
                    raise ZipFileParsingException('El fichero {} no contiene el campo "type"'.format(__JSON_NAME))
                if json_problem_type != problem_type:
                    raise ZipFileParsingException(f'Campo "type" del fichero {__JSON_NAME} incorrecto: '
                                                  f'esperaba {problem_type} y se ha leído {json_problem_type}')
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {}".format(type(e), e))
    return problem_json


def load_select_problem(problem, file):
    """
    Load the problem information form a ZIP file and updates the attributes of 'problem'
    :param problem: SelectProblem to update
    :param file: ZipFile previamente abierto y con fichero JSON
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Comprobando existencia de ficheros'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __SELECT_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    'El problema debe contener al menos los siguientes ficheros: {}'.format(__SELECT_PROBLEM_FILES))

            state = 'Leyendo fichero JSON'
            problem.title_md = problem_json.get('title', '')
            problem.min_stmt = int(problem_json['min_stmt'])
            problem.max_stmt = int(problem_json['max_stmt'])
            problem.position = int(problem_json['position'])
            problem.check_order = bool(problem_json.get('check_order'))  # None will be converted to False
            if (not problem.title_md or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                    problem.min_stmt > problem.max_stmt):
                raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", "min_stmt", '
                                              '"max_stmt" o "position')

            state = 'Leyendo fichero text.md'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode()

            state = 'Leyendo fichero create.sql'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode()
                problem.create_sql = create_str

            state = 'Leyendo fichero insert.sql'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode()
                problem.insert_sql = insert_str

            state = 'Leyendo fichero solution.sql'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode()
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def load_dml_problem(problem, file):
    """
    Load the problem information form a ZIP file and updates the attributes of 'problem'
    :param problem: DMLProblem to update
    :param file: ZipFile previamente abierto y con fichero JSON
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Comprobando existencia de ficheros'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __DML_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    'El problema debe contener al menos los siguientes ficheros: {}'.format(__DML_PROBLEM_FILES))

            state = 'Leyendo fichero JSON'
            problem.title_md = problem_json.get('title', '')
            problem.min_stmt = int(problem_json['min_stmt'])
            problem.max_stmt = int(problem_json['max_stmt'])
            problem.position = int(problem_json['position'])
            if (not problem.title_md or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                    problem.min_stmt > problem.max_stmt):
                raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", "min_stmt", '
                                              '"max_stmt" o "position')

            state = 'Leyendo fichero text.md'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode()

            state = 'Leyendo fichero create.sql'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode()
                problem.create_sql = create_str

            state = 'Leyendo fichero insert.sql'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode()
                problem.insert_sql = insert_str

            state = 'Leyendo fichero solution.sql'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode()
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def load_function_problem(problem, file):
    """
    Load the problem information form a ZIP file and updates the attributes of 'problem'
    :param problem: DMLProblem to update
    :param file: ZipFile previamente abierto y con fichero JSON
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Comprobando existencia de ficheros'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    'El problema debe contener al menos los siguientes ficheros: {}'.format(__FUNCTION_PROBLEM_FILES))

            state = 'Leyendo fichero JSON'
            problem.title_md = problem_json.get('title', '')
            problem.position = int(problem_json['position'])
            if not problem.title_md:
                raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", o "position"')

            state = 'Leyendo fichero text.md'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode()

            state = 'Leyendo fichero create.sql'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode()
                problem.create_sql = create_str

            state = 'Leyendo fichero insert.sql'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode()
                problem.insert_sql = insert_str

            state = 'Leyendo fichero solution.sql'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode()

            state = 'Leyendo fichero tests.sql'
            with zfile.open('tests.sql', 'r') as tests_file:
                problem.calls = tests_file.read().decode()
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def load_proc_problem(problem, file):
    """
    Load the problem information form a ZIP file and updates the attributes of 'problem'
    :param problem: DMLProblem to update
    :param file: ZipFile previamente abierto y con fichero JSON
    :return: None or raise ZipFileParsingException if there is any problem
    """
    state = 'Comprobando existencia de ficheros'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    'El problema debe contener al menos los siguientes ficheros: {}'.format(__PROC_PROBLEM_FILES))

            state = 'Leyendo fichero JSON'
            problem.title_md = problem_json.get('title', '')
            problem.position = int(problem_json['position'])
            if not problem.title_md:
                raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", o "position"')

            state = 'Leyendo fichero text.md'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode()

            state = 'Leyendo fichero create.sql'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode()
                problem.create_sql = create_str

            state = 'Leyendo fichero insert.sql'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode()
                problem.insert_sql = insert_str

            state = 'Leyendo fichero solution.sql'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode()

            state = 'Leyendo fichero tests.sql'
            with zfile.open('tests.sql', 'r') as tests_file:
                problem.proc_call = tests_file.read().decode().strip()
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def load_trigger_problem(problem, file):
    """
        Load the problem information form a ZIP file and updates the attributes of 'problem'
        :param problem: DMLProblem to update
        :param file: ZipFile previamente abierto y con fichero JSON
        :return: None or raise ZipFileParsingException if there is any problem
        """
    state = 'Comprobando existencia de ficheros'
    try:
        problem_json = extract_json(file, problem.problem_type())
        with ZipFile(file) as zfile:
            if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
                raise ZipFileParsingException(
                    'El problema debe contener al menos los siguientes ficheros: {}'.format(__TRIGGER_PROBLEM_FILES))

            state = 'Leyendo fichero JSON'
            problem.title_md = problem_json.get('title', '')
            problem.position = int(problem_json['position'])
            if not problem.title_md:
                raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", o "position"')

            state = 'Leyendo fichero text.md'
            with zfile.open('text.md', 'r') as text_file:
                problem.text_md = text_file.read().decode()

            state = 'Leyendo fichero create.sql'
            with zfile.open('create.sql', 'r') as create_file:
                create_str = create_file.read().decode()
                problem.create_sql = create_str

            state = 'Leyendo fichero insert.sql'
            with zfile.open('insert.sql', 'r') as insert_file:
                insert_str = insert_file.read().decode()
                problem.insert_sql = insert_str

            state = 'Leyendo fichero solution.sql'
            with zfile.open('solution.sql', 'r') as solution_file:
                problem.solution = solution_file.read().decode()

            state = 'Leyendo fichero tests.sql'
            with zfile.open('tests.sql', 'r') as tests_file:
                problem.tests = tests_file.read().decode().strip()
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


