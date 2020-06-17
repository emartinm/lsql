# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Utility functions to check the the input from the user is well-formed
"""
import os

from zipfile import ZipFile
import sqlparse
import json
import markdown
from django.core.exceptions import ValidationError
from lxml import html
import tempfile

from .models import SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem
from .exceptions import ZipFileParsingException, ExecutorException
from .types import ProblemType

__MAX_INT = 2 ** 31
__MIN_INT = -(2 ** 31)
__JSON_NAME = 'problem.json'
__SELECT_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md'}
__DML_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md'}
__FUNCTION_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__PROC_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}
__TRIGGER_PROBLEM_FILES = {'create.sql', 'insert.sql', 'problem.json', 'solution.sql', 'text.md', 'tests.sql'}


def ucm_email(_, field):
    if not field.data.endswith('@ucm.es'):
        raise ValidationError('Not an UCM e-mail address')


def markdown_to_html(md, remove_initial_p=False):
    html_code = markdown.markdown(md, output_format='html5').strip()
    tree = html.fromstring(html_code)
    if remove_initial_p and tree.tag == 'p':
        # Removes the surrounding <p></p> in one paragraph html
        html_code = html_code[3:-4]
    return html_code


def parse_many_problems(file, oracle, col_id, author):
    problems = list()
    tmp_file = tempfile.mkstemp(suffix='.zip', prefix='lsql_')[1]
    try:
        with ZipFile(file) as zf:
            for filename in zf.infolist():
                # Workaround to avoid unexpected BadZipFile exceptions when opening ZIP files inside 'file'
                # Now I first save the ZIP file to a temp file and use that path to parse each problem
                curr_file = FileStorage(zf.open(filename), content_type='application/zip')
                curr_file.save(tmp_file)
                problem = parse_problem(tmp_file, oracle)
                problem.collection = col_id
                problem.author = author
                problems.append(problem)
    except ZipFileParsingException as e:
        raise ZipFileParsingException('{}: {}'.format(filename.filename, e))
    except Exception as e:
        raise ZipFileParsingException("{}: {}".format(type(e), e))
    finally:
        # It will always exist, as it is created with mkstemp
        os.remove(tmp_file)
    return problems


def parse_problem(file, oracle):
    """

    :param oracle:
    :param file: werkzeug.datastructures.FileStorage or path (str)
    :return: Object of a subclass of lsql.database_dao.Problem
    """
    problem = dict()
    try:
        with ZipFile(file) as zfile:
            if __JSON_NAME not in zfile.namelist():
                raise ZipFileParsingException('Falta el fichero {}'.format(__JSON_NAME))

            with zfile.open(__JSON_NAME, 'r') as jsonfile:
                problem_json = json.load(jsonfile)

                problem_type = problem_json.get('type', None)
                if problem_type is None:
                    raise ZipFileParsingException('El fichero {} no contiene el campo "type"'.format(__JSON_NAME))
                problem = parse_problem_type(zfile, problem_json, problem_type, oracle)
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {}".format(type(e), e))

    return problem


def parse_problem_type(zfile, problem_json, problem_type, oracle):
    # mapping Problem Type -> parsing function
    mapping = {ProblemType.SELECT: parse_select_problem,
               ProblemType.DML: parse_dml_problem,
               ProblemType.FUNCTION: parse_function_problem,
               ProblemType.PROC: parse_proc_problem,
               ProblemType.TRIGGER: parse_trigger_problem}
    try:
        return mapping[problem_type](zfile, problem_json, oracle)
    except KeyError:
        raise ZipFileParsingException('Tipo de problema no soportado: "type: {}"'.format(problem_type))


def parse_select_problem(zfile, problem_json, oracle):
    """

    :param oracle:
    :param zfile: ZipFile previamente abierto y con fichero JSON
    :param problem_json: dict() con el contenido del fichero JSON
    :return: dict o raise ZipFileParsingException si hay algún problema
    """
    state = 'Comprobando existencia de ficheros'
    try:
        if not __SELECT_PROBLEM_FILES <= set(zfile.namelist()):
            raise ZipFileParsingException(
                'El problema debe contener al menos los siguientes ficheros: {}'.format(__SELECT_PROBLEM_FILES))

        problem = SelectProblem()

        state = 'Leyendo fichero JSON'
        problem.title = markdown_to_html(problem_json.get('title', ''), remove_initial_p=True)
        problem.min_stmt = int(problem_json['min_stmt'])
        problem.max_stmt = int(problem_json['max_stmt'])
        problem.position = int(problem_json['position'])
        problem.check_order = bool(problem_json.get('check_order'))  # None will be converted to False
        if (not problem.title or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                problem.min_stmt > problem.max_stmt):
            raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", "min_stmt", '
                                          '"max_stmt" o "position')

        state = 'Leyendo fichero text.md'
        with zfile.open('text.md', 'r') as text_file:
            problem.text = markdown_to_html(text_file.read().decode())

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
            solution_str = solution_file.read().decode()
            problem.correct_select = solution_str

        state = 'Ejecutando ficheros SQL'
        try:
            res = oracle.execute_select_test(create_str, insert_str, solution_str, output_db=True)
        except ExecutorException as e:
            raise ZipFileParsingException(
                f'Error al ejecutar los ficheros SQL: <<codigo LSQL: {e.error_code}>> - <<Causa: {e.message}>>')

        problem.initial_db = res['db']
        problem.expected_result = res['result']
        return problem
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def parse_dml_problem(zfile, problem_json, oracle):
    """

    :param oracle:
    :param zfile: ZipFile previamente abierto y con fichero JSON
    :param problem_json: dict() con el contenido del fichero JSON
    :return: dict o raise ZipFileParsingException si hay algún problema
    """
    state = 'Comprobando existencia de ficheros'
    try:
        if not __DML_PROBLEM_FILES <= set(zfile.namelist()):
            raise ZipFileParsingException(
                'El problema debe contener al menos los siguientes ficheros: {}'.format(__DML_PROBLEM_FILES))

        problem = DMLProblem()

        state = 'Leyendo fichero JSON'
        problem.title = markdown_to_html(problem_json.get('title', ''), remove_initial_p=True)
        problem.min_stmt = int(problem_json['min_stmt'])
        problem.max_stmt = int(problem_json['max_stmt'])
        problem.position = int(problem_json['position'])
        if (not problem.title or problem.min_stmt <= 0 or problem.max_stmt <= 0 or
                problem.min_stmt > problem.max_stmt):
            raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", "min_stmt", '
                                          '"max_stmt" o "position')

        state = 'Leyendo fichero text.md'
        with zfile.open('text.md', 'r') as text_file:
            problem.text = markdown_to_html(text_file.read().decode())

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
            solution_str = solution_file.read().decode()
            problem.correct_dml = solution_str

        state = 'Ejecutando ficheros SQL'
        try:
            res = oracle.execute_dml_test(create_str, insert_str, solution_str, pre_db=True)
        except ExecutorException as e:
            raise ZipFileParsingException(
                f'Error al ejecutar los ficheros SQL: <<codigo LSQL: {e.error_code}>> - <<Causa: {e.message}>>')

        problem.initial_db = res['pre']
        problem.expected_result = res['post']
        return problem
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def parse_function_problem(zfile, problem_json, oracle):
    """

    :param oracle:
    :param zfile: ZipFile previamente abierto y con fichero JSON
    :param problem_json: dict() con el contenido del fichero JSON
    :return: dict o raise ZipFileParsingException si hay algún problema
    """
    state = 'Comprobando existencia de ficheros'
    try:
        if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
            raise ZipFileParsingException(
                'El problema debe contener al menos los siguientes ficheros: {}'.format(__DML_PROBLEM_FILES))

        problem = FunctionProblem()

        state = 'Leyendo fichero JSON'
        problem.title = markdown_to_html(problem_json.get('title', ''), remove_initial_p=True)
        problem.position = int(problem_json['position'])
        if not problem.title:
            raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", o "position"')

        state = 'Leyendo fichero text.md'
        with zfile.open('text.md', 'r') as text_file:
            problem.text = markdown_to_html(text_file.read().decode())

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
            solution_str = solution_file.read().decode()
            problem.correct_function_definition = solution_str

        state = 'Leyendo fichero tests.sql'
        with zfile.open('tests.sql', 'r') as tests_file:
            tests_str = tests_file.read().decode()
            tests_list = tests_str.split('\n')
            tests_list = [s.strip() for s in tests_list if len(s.strip()) > 0]

        state = 'Ejecutando ficheros SQL'
        try:
            res = oracle.execute_function_test(create_str, insert_str, solution_str, tests_list)
        except ExecutorException as e:
            raise ZipFileParsingException(
                f'Error al ejecutar los ficheros SQL: <<codigo LSQL: {e.error_code}>> - <<Causa: {e.message}>>')

        problem.initial_db = res['db']
        problem.expected_result = res['results']
        return problem
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def parse_proc_problem(zfile, problem_json, oracle):
    """

    :param oracle:
    :param zfile: ZipFile previamente abierto y con fichero JSON
    :param problem_json: dict() con el contenido del fichero JSON
    :return: dict o raise ZipFileParsingException si hay algún problema
    """
    state = 'Comprobando existencia de ficheros'
    try:
        if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
            raise ZipFileParsingException(
                'El problema debe contener al menos los siguientes ficheros: {}'.format(__DML_PROBLEM_FILES))

        problem = ProcProblem()

        state = 'Leyendo fichero JSON'
        problem.title = markdown_to_html(problem_json.get('title', ''), remove_initial_p=True)
        problem.position = int(problem_json['position'])
        if not problem.title:
            raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", o "position"')

        state = 'Leyendo fichero text.md'
        with zfile.open('text.md', 'r') as text_file:
            problem.text = markdown_to_html(text_file.read().decode())

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
            solution_str = solution_file.read().decode()
            problem.correct_proc_definition = solution_str

        state = 'Leyendo fichero tests.sql'
        with zfile.open('tests.sql', 'r') as tests_file:
            tests_str = tests_file.read().decode().strip()
            problem.proc_call = tests_str

        state = 'Ejecutando ficheros SQL'
        try:
            res = oracle.execute_proc_test(create_str, insert_str, solution_str, tests_str)
        except ExecutorException as e:
            raise ZipFileParsingException(
                f'Error al ejecutar los ficheros SQL: <<codigo LSQL: {e.error_code}>> - <<Causa: {e.message}>>')

        problem.initial_db = res['pre']
        problem.expected_result = res['post']
        return problem
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))


def parse_trigger_problem(zfile, problem_json, oracle):
    """

    :param oracle:
    :param zfile: ZipFile previamente abierto y con fichero JSON
    :param problem_json: dict() con el contenido del fichero JSON
    :return: dict o raise ZipFileParsingException si hay algún problema
    """
    state = 'Comprobando existencia de ficheros'
    try:
        if not __FUNCTION_PROBLEM_FILES <= set(zfile.namelist()):
            raise ZipFileParsingException(
                'El problema debe contener al menos los siguientes ficheros: {}'.format(__DML_PROBLEM_FILES))

        problem = TriggerProblem()

        state = 'Leyendo fichero JSON'
        problem.title = markdown_to_html(problem_json.get('title', ''), remove_initial_p=True)
        problem.position = int(problem_json['position'])
        if not problem.title:
            raise ZipFileParsingException('Valores erróneos en los campos del fichero JSON: "title", o "position"')

        state = 'Leyendo fichero text.md'
        with zfile.open('text.md', 'r') as text_file:
            problem.text = markdown_to_html(text_file.read().decode())

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
            solution_str = solution_file.read().decode()
            problem.correct_trigger_definition = solution_str

        state = 'Leyendo fichero tests.sql'
        with zfile.open('tests.sql', 'r') as tests_file:
            tests_str = tests_file.read().decode().strip()
            problem.tests = tests_str

        state = 'Ejecutando ficheros SQL'
        try:
            res = oracle.execute_trigger_test(create_str, insert_str, solution_str, tests_str)
        except ExecutorException as e:
            raise ZipFileParsingException(
                f'Error al ejecutar los ficheros SQL: <<codigo LSQL: {e.error_code}>> - <<Causa: {e.message}>>')

        problem.initial_db = res['pre']
        problem.expected_result = res['post']
        return problem
    except ZipFileParsingException:
        raise
    except Exception as e:
        raise ZipFileParsingException("{}: {} - {}".format(state, type(e), e))
