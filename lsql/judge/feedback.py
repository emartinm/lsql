# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Generation of feedback messages
"""
import re

from django.template.loader import render_to_string
from multiset import Multiset

from .types import VeredictCode

__ORACLE_TYPE_PATTERN_VERSION_7 = r"<class 'cx_Oracle\.(.*)'>"
__ORACLE_TYPE_PATTERN_VERSION_8 = r"<cx_Oracle\.DbType (.*)>"


def pretty_type(type_str):
    """Given a string representing a type of cx_Oracle (https://cx-oracle.readthedocs.io/en/latest/api_manual/
    module.html?highlight=cx_Oracle.DbType%20DB_TYPE_CHAR#database-types), extracts the important fragment
    Adapted to support cx_Oracle v8 types as '<cx_Oracle.DbType DB_TYPE_CHAR>' as well as deprecated cx_Oracle v7 types
    """
    match = re.match(__ORACLE_TYPE_PATTERN_VERSION_8, type_str)
    if match:
        return match.group(1)
    match = re.match(__ORACLE_TYPE_PATTERN_VERSION_7, type_str)
    if match:
        return match.group(1)
    return type_str


def header_to_str(header):
    """
    Transform a list of lists of two elements [name, cx_Oracle type] in a pretty string
    :param header: Something like [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]]
    :return: (str) Pretty version like "(ID: NUMBER, NOMBRE: STRING)"
    """
    columns = list()
    for name, oracle_type in header:
        columns.append("{}: {}".format(name, pretty_type(oracle_type)))
    str_header = ", ".join(columns)
    return "(" + str_header + ")"


def feedback_headers(expected, obtained, initial_db=None):
    """
    :param expected: expected result ({'header': list, 'rows': list})
    :param obtained: obtained result ({'header': list, 'rows': list})
    :param initial_db: List containing all tables
    :return: (str) HTML code with the feedback, or '' if the headers are equal
    """

    if expected['header'] == obtained['header']:
        return ''

    if len(expected['header']) != len(obtained['header']):
        _expected = f"Esperado: {len(expected['header'])} columnas"
        _obtained = f"Generado por tu código SQL: {len(obtained['header'])} columnas"
        comment = "Número de columnas obtenidas:"
        return render_to_string('feedback_wa_headers.html',
                                {'expected': _expected,
                                 'comment': comment,
                                 'expected_rows': header_to_str(expected['header']),
                                 'obtained_rows': header_to_str(obtained['header']),
                                 'obtained': _obtained,
                                 'initial_db': initial_db}
                                )

    longitud = len(expected['header'])
    i = 0
    while i < longitud:
        name_expected = expected['header'][i][0]
        oracle_type_expected = pretty_type(expected['header'][i][1])
        name_obtained = obtained['header'][i][0]
        oracle_type_obtained = pretty_type(obtained['header'][i][1])
        if name_expected.upper() != name_obtained.upper():
            expected_r = f"Nombre esperado: {name_expected}"
            obtained_r = f"Nombre generado por tu código SQL: {name_obtained}"
            comment = f"nombre de la {i+1}ª columna"
            return render_to_string('feedback_wa_headers.html',
                                    {'expected': expected_r,
                                     'comment': comment,
                                     'obtained': obtained_r,
                                     'initial_db': initial_db}
                                    )
        if name_expected.upper() == name_obtained.upper() and \
                oracle_type_expected.upper() != oracle_type_obtained.upper():
            expected_r2 = f"Tipo esperado: {oracle_type_expected}"
            obtained_r2 = f"Tipo generado por tu código SQL: {oracle_type_obtained}"
            comment2 = f"tipo de la columna {name_expected}:"
            return render_to_string('feedback_wa_headers.html',
                                    {'expected': expected_r2,
                                     'comment': comment2,
                                     'obtained': obtained_r2,
                                     'initial_db': initial_db}
                                    )
        i = i + 1
    return ''


def feedback_rows(expected, obtained, order, initial_db=None):
    """
    :param expected: expected result ({'header': list, 'rows': list})
    :param obtained: obtained result ({'header': list, 'rows': list})
    :param order: consider order when comparing rows
    :param initial_db: List containing all tables
    :return: (str) HTML code with the feedback, or '' if the table rows are equal (considering order)
    """
    tupled_expected = [tuple(r) for r in expected['rows']]
    tupled_obtained = [tuple(r) for r in obtained['rows']]
    mset_expected = Multiset(tupled_expected)
    mset_obtained = Multiset(tupled_obtained)
    obtained_not_expected = mset_obtained - mset_expected

    if obtained_not_expected:
        # Some rows are not expected, get row numbers to mark them in the feedback
        incorrect_row_numbers = set()  # Starting from 0
        pos = 0
        while pos < len(tupled_obtained) and obtained_not_expected:
            if tupled_obtained[pos] in obtained_not_expected:
                incorrect_row_numbers.add(pos)
                obtained_not_expected.remove(tupled_obtained[pos], 1)  # Removes one appearance of that row
            pos = pos + 1
        feedback = render_to_string('feedback_wa_wrong_rows.html',
                                    {'table': {'header': expected['header'], 'rows': tupled_obtained},
                                     'name': None,
                                     'mark_rows': incorrect_row_numbers,
                                     'initial_db': initial_db}
                                    )
        return feedback

    expected_not_obtained = mset_expected - mset_obtained
    if expected_not_obtained:
        feedback = render_to_string('feedback_wa_missing_rows.html',
                                    {'obtained': obtained,
                                     'missing': {'header': expected['header'], 'rows': expected_not_obtained},
                                     'mark_missing': set(list(range(len(expected_not_obtained)))),
                                     'initial_db': initial_db}
                                    )
        return feedback

    if order and expected != obtained:
        return render_to_string('feedback_wa_order.html', {'expected': expected, 'obtained': obtained})

    return ''  # Everything OK => Accepted


def compare_select_results(expected, obtained, order, initial_db=None):
    """
    :param expected: {'header': list, 'rows': list}, expected SELECT result (teacher).
    :param obtained: {'header': list, 'rows': list}, obtained SELECT result (student)
    :param order: Consider order when comparing rows
    :param initial_db: List containing all tables
    :return: (veredict, feedback), where veredict is VeredictCode.AC or VeredictCode.WA and
             error is a str with feedback to the student
    """
    parsed_initial_db = None
    if initial_db is not None:
        parsed_initial_db = []
        for table_name in initial_db:
            tupled_obtained = [tuple(r) for r in initial_db[table_name]['rows']]
            parsed_initial_db.append({'header': initial_db[table_name]['header'], 'rows': tupled_obtained})
    feedback = feedback_headers(expected, obtained, parsed_initial_db)
    if not feedback:
        feedback = feedback_rows(expected, obtained, order, parsed_initial_db)
    veredict = VeredictCode.WA if feedback else VeredictCode.AC
    return veredict, feedback


def compare_discriminant_db(correct, incorrect, order):
    """Compare the two db from discriminant type problem"""
    feedback = feedback_headers(correct, incorrect, None)
    if not feedback:
        feedback = feedback_rows_discriminant(correct, incorrect, order)
    veredict = VeredictCode.WA if feedback else VeredictCode.AC
    return veredict, feedback


def feedback_rows_discriminant(correct, incorrect, order):
    """
    :param correct: expected result ({'header': list, 'rows': list})
    :param incorrect: obtained result ({'header': list, 'rows': list})
    :param order: consider order when comparing rows
    :return: (str) HTML code with the feedback, or '' if the table rows are not equal (considering order)
    """
    tupled_correct = [tuple(r) for r in correct['rows']]
    tupled_incorrect = [tuple(r) for r in incorrect['rows']]
    mset_correct = Multiset(tupled_correct)
    mset_incorrect = Multiset(tupled_incorrect)
    obtained_not_expected = mset_correct - mset_incorrect
    if (order and correct != incorrect) or obtained_not_expected:
        return ''
    return render_to_string('feedback_table_result.html', {'obtained': incorrect})


def compare_db_results(expected_db, obtained_db):
    """
    Given an expected DB and an obtained DB, returns a veredict of the comparison and its HTML feedback
    :param expected_db: dict {table_name: dict}
    :param obtained_db: dict {table_name: dict}
    :return: (VeredictCode, str)
    """
    feedback = ''
    expected_tables = set(expected_db.keys())
    obtained_tables = set(obtained_db.keys())

    if expected_tables != obtained_tables:
        obtained = sorted(list(obtained_db.keys()))
        expected = sorted(list(expected_db.keys()))
        return VeredictCode.WA, render_to_string('feedback_wa_tables.html',
                                                 {'obtained': obtained, 'expected': expected})

    veredict = VeredictCode.AC
    for table in expected_db:
        veredict, feedback = compare_select_results(expected_db[table], obtained_db[table], order=False)
        if veredict != VeredictCode.AC:
            feedback = f"<h4>La tabla <code>{table}</code> es incorrecta:</h4>{feedback}"
            break
    return veredict, feedback


def compare_function_results(expected, obtained):
    """
    Given an expected DB and an obtained DB, returns a veredict of the comparison and its HTML feedback
    :param expected: dict {call: result}
    :param obtained: dict {call: result}
    :return: (VeredictCode, str)
    """
    veredict = VeredictCode.AC
    feedback = ''
    for call in expected:
        if expected[call] != obtained[call]:
            veredict = VeredictCode.WA
            feedback = render_to_string('feedback_wa_function.html',
                                        {'call': call, 'expected': expected[call], 'obtained': obtained[call]})
            break
    return veredict, feedback


def compile_error_to_html_table(tab):
    """
    Generates the wrong answer HTML response from a SQL table included in the COMPILE_ERROR exception
    :param tab: dictionary with header and rows
    :return: HTML message
    """
    feedback = render_to_string('feedback_ce.html', {'table': tab})
    return feedback


def filter_expected_db(expected_db, initial_db):
    """Compare expected_db and initial_db and return all the modified, removed or added tables"""
    expected_tables = sorted(list(expected_db.keys()))
    initial_tables = sorted(list(initial_db.keys()))
    ret_added = {}
    ret_modified = {}
    ret_removed = {}
    common_tables = initial_db.keys() & expected_db.keys()
    if expected_tables != initial_tables:
        ret_added = {x: expected_db[x] for x in expected_tables if x not in initial_tables}
        ret_removed = {x: initial_db[x] for x in initial_tables if x not in expected_tables}
    for table in common_tables:
        veredict, _ = compare_select_results(expected_db[table], initial_db[table], order=False)
        if veredict != VeredictCode.AC:
            ret_modified[table] = expected_db[table]
    return ret_added, ret_modified, ret_removed
