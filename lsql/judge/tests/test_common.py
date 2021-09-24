# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Common function and constants for testing
"""
from datetime import datetime

import django.contrib.auth
from django.contrib.auth.models import Group

from judge.models import Hint, UsedHint, Submission, DiscriminantProblem, SelectProblem, DMLProblem, Collection


class TestPaths:  # pylint: disable=too-few-public-methods
    """ Class only to store paths for testing files """
    ZIP_FOLDER = 'zip_files'

    MANY_PROBLEMS_ZIP_NAME = 'problems.zip'

    NO_JSON = 'no_json.zip'
    JSON_DECODE_ERROR = 'select_json_decode_error.zip'
    WRONG_TYPE = 'select_json_invalid_type.zip'
    NO_TYPE = 'no_type.zip'

    SELECT_OK = 'select_ok.zip'
    SELECT_LARGE = 'select_very_large.zip'
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


def create_hint(problem, id_hint, num_submissions):
    """ Creates and stores a Hint of a Problem """
    description = f'descripcion de la pista {id_hint}'
    hint = Hint(text_md=description, problem=problem, num_submit=num_submissions)
    hint.save()
    return hint


def create_used_hint(hint, user):
    """ Creates and stores a used Hint of a Problem """
    used_hint = UsedHint(user=user, request_date=datetime(2020, 3, 5), hint_definition=hint)
    used_hint.save()
    return used_hint


def create_discriminant_problem(important_order, collection, name='Ejemplo'):
    """Creates and stores a Discriminant DB Problem"""
    if not important_order:
        create = 'CREATE TABLE test_table_1 (n NUMBER);'
        insert = "INSERT INTO test_table_1 VALUES (1997);"
        incorrect = 'SELECT * FROM test_table_1;'
        correct = 'SELECT * FROM test_table_1 WHERE n > 1000;'
    else:
        create = 'CREATE TABLE test_table_1 (x NUMBER, n NUMBER);'
        insert = "INSERT INTO test_table_1 VALUES (1997, 1997);\
                  INSERT INTO test_table_1  VALUES (1994, 1994);"
        correct = 'SELECT * FROM test_table_1 ORDER BY n ASC'
        incorrect = 'SELECT * FROM test_table_1 ORDER BY x ASC'
    problem = DiscriminantProblem(title_md=name, text_md='texto largo', create_sql=create, insert_sql=insert,
                                  correct_query=correct, incorrect_query=incorrect, check_order=important_order,
                                  collection=collection)
    problem.clean()
    problem.save()
    return problem


def create_select_problem(collection, name='Ejemplo'):
    """ Creates and stores a Select Problem """
    create = 'CREATE TABLE test (n NUMBER);'
    insert = "INSERT INTO test VALUES (901)"
    solution = 'SELECT * FROM test'
    problem = SelectProblem(title_md=name, text_md='texto largo',
                            create_sql=create, insert_sql=insert, collection=collection,
                            solution=solution)
    problem.clean()
    problem.save()
    return problem


def create_dml_problem(collection, name='Ejemplo'):
    """Creates and stores a DML Problem accepting between 2 and 3 SQL sentences"""
    create = 'CREATE TABLE test (n NUMBER);'
    insert = "INSERT INTO test VALUES (901)"
    solution = 'INSERT INTO test VALUES (25); INSERT INTO test VALUES (50); INSERT INTO test VALUES (75);'
    problem = DMLProblem(title_md=name, text_md='texto largo',
                         create_sql=create, insert_sql=insert, collection=collection,
                         solution=solution, min_stmt=2, max_stmt=3)
    problem.clean()
    problem.save()
    return problem


def create_dml_complete_problem(collection, name='Ejemplo'):
    """Creates and stores a DML Problem with an INSERT, a DELETE, a DROP and CREATE"""
    create = 'CREATE TABLE test_table_1 (n NUMBER);\
             CREATE TABLE test_table_2 (n NUMBER);\
             CREATE TABLE test_table_3 (n NUMBER);'
    insert = "INSERT INTO test_table_1 VALUES (1997);\
             INSERT INTO test_table_2 VALUES (14);\
             INSERT INTO test_table_3 VALUES (17);\
             INSERT INTO test_table_3 VALUES (83)"
    solution = 'INSERT INTO test_table_1 VALUES (312);\
               DELETE FROM test_table_3 WHERE n = 83;\
               CREATE TABLE new (n NUMBER);\
               DROP TABLE test_table_2;'
    problem = DMLProblem(title_md=name, text_md='texto largo',
                         create_sql=create, insert_sql=insert, collection=collection,
                         solution=solution, min_stmt=2, max_stmt=10)
    problem.clean()
    problem.save()
    return problem


def create_collection(name='Prueba', visibility=True, author=None):
    """Creates and stores a collection"""
    collection = Collection(name_md=name, description_md='texto explicativo', visible=visibility, author=author)
    collection.clean()
    collection.save()
    return collection


def create_user(passwd, username='usuario'):
    """Creates and stores a user"""
    user = django.contrib.auth.get_user_model().objects.create_user(
        username=username,
        email='email@ucm.es',
        password=passwd)
    return user


def create_superuser(passwd, username='staff'):
    """Creates and stores a super user"""
    user = django.contrib.auth.get_user_model().objects.create_superuser(
        username=username,
        password=passwd)
    return user


def create_group(name='nombre'):
    """Creates and stores a group"""
    group = Group.objects.create(name=name)
    return group


def create_submission(problem, user, verdict, code='nada'):
    """Creates and stores a submission"""
    sub = Submission(code=code, verdict_code=verdict, user=user, problem=problem)
    sub.clean()
    sub.save()
    return sub
