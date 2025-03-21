# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Methods for batch processing that can be invoked from the shell (python manage.py shell).
For example: create a group of users from a CSV list of students
"""

import csv
import datetime
import secrets
import sqlglot

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count, Min, Max

from .models import Problem, Submission
from .types import ProblemType


def create_users_from_csv(csv_filename: str, group_name: str, dry: bool = False):
    """
    Batch creation of users from a CSV file, each line representing a new user. The username is the
    first part of the email (before @) and the password is the document number. Assigns every new
    user to a new created group with name 'group_name'

    If dry = True does not modify the DB but only show messages of the actions

    Each line has the following fields:
      FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,MAT.,CONV.,OBSERVACIÓN,CORREO,TELÉFONO
    """
    if dry:
        print('Creating users from CSV (DRY RUN): NO USERS OR GROUPS WILL BE SAVED!')
        group = Group(name=group_name)  # Dummy group not saved for dry run
    else:
        print('Creating users from CSV')
        group = Group.objects.create(name=group_name)
    print(f'* Created group {group_name}')
    with open(csv_filename, encoding='utf_8') as csvfile:
        reader = csv.DictReader(csvfile)
        create_users_from_list(reader, group, dry)
    print()


def create_users_from_list(dict_list, group: Group, dry: bool):
    """
    Batch creation of users from a list of dictionaries, each dictionary representing a new user. The username is the
    first part of the email (before @) and the password is the document number.

    If dry = True does not modify the DB but only show messages of the actions

    Dictionaries have the following keys:
      FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,MAT.,CONV.,OBSERVACIÓN,CORREO,TELÉFONO
    """
    if not group:
        raise AssertionError  # Group is set
    for user_dict in dict_list:
        email = user_dict['CORREO']
        if not email:
            raise AssertionError
        if not email.split('@')[1] == 'ucm.es':
            raise AssertionError  # We want official UCM emails
        username = email.split('@')[0]
        password = user_dict['DOCUMENTO']
        if ',' in user_dict['NOMBRE COMPLETO']:
            first_name = user_dict['NOMBRE COMPLETO'].split(',')[1].strip()
            last_name = user_dict['NOMBRE COMPLETO'].split(',')[0].strip()
        else:
            first_name = user_dict['NOMBRE COMPLETO']
            last_name = '_'

        # Safety checks
        if not username:
            raise AssertionError
        if not password:
            raise AssertionError
        if not first_name:
            raise AssertionError
        if not last_name:
            raise AssertionError

        if not dry:
            user = get_user_model().objects.create_user(username, email, password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            group.user_set.add(user)
        print(f'* Saved User("username:{username}", email:"{email}", passwd:"{password}", '
              f'first_name:"{first_name}", last_name:"{last_name}") in group "{group}"')


def is_list_of_dict(value):
    """ Check if value is a non-empty list of dictionaries """
    return isinstance(value, list) and len(value) > 0 and all(isinstance(elem, dict) for elem in value)


def adapt_db_result_to_list():
    """ Adapts the fields 'initial_db' and 'expected_result' in the problems from dictionaries to
        unitary lists containing that dictionary """
    for prob in Problem.objects.all().select_subclasses():
        # We need to traverse the different types of problems because expected_result is defined in the
        # child classes, not in Problem.
        if isinstance(prob.initial_db, dict):
            prob.initial_db = [prob.initial_db]
        elif not is_list_of_dict(prob.initial_db):
            raise TypeError(f"Unexpected initial_db type: {prob.initial_db}")

        if isinstance(prob.expected_result, dict):
            prob.expected_result = [prob.expected_result]
        elif not is_list_of_dict(prob.expected_result):
            raise TypeError(f"Unexpected expected_result type: {prob.expected_result}")
        prob.save()


def rejudge(verdict_code, filename='rejudge.txt', tests=False,
            start=datetime.datetime(1970, 1, 1).astimezone(),
            end=timezone.now()):
    """ Judges again all the submission in the period [start, end] with some verdict_code. For each submission,
        submit the code, compares the verdict, and stores detailed information in the 'filename'.
        Use tests=False for Django tests, tests=True for normal use
    """
    username = f'rejudge_user_test_{secrets.token_hex(nbytes=8)}'
    passwd = secrets.token_hex(nbytes=16)
    user = None

    try:
        subs = Submission.objects.filter(verdict_code=verdict_code, creation_date__gte=start, creation_date__lte=end)
        rejudge_users = get_user_model().objects.filter(username=username)
        # In case the user was not deleted in a previous execution
        user = (rejudge_users[0] if len(rejudge_users) == 1 else
                get_user_model().objects.create_user(username=username, password=passwd))
        client = Client()
        client.login(username=username, password=passwd)

        changes = {}
        with open(filename, 'w', encoding='utf8') as report:
            for sub in subs:
                submit_url = reverse('judge:submit', args=[sub.problem.pk])
                # Using Client outside the Django testing command requires adjustment in the HTTP Host header
                http_host = '127.0.0.1' if settings.DEBUG else 'learn.fdi.ucm.es'
                response = client.post(submit_url, {'code': sub.code}, HTTP_HOST=http_host, follow=True) if not tests \
                    else client.post(submit_url, {'code': sub.code}, follow=True)
                report.write(f'Submission #{sub.pk}\n')
                report.write('----------------------------\n')
                report.write(f'Problem: {sub.problem.pk}\n')
                report.write(f'User: {sub.user}\n')
                report.write(f'Date: {sub.creation_date}\n')
                report.write(f'Code ({len(sub.code)} chars):\n{sub.code}\n')
                response_json = response.json()
                verdict_change = f'{sub.verdict_code} --> {response_json["verdict"]}'
                report.write(f'Verdict: {verdict_change}\n')
                report.write(f'New feedback: {response_json["feedback"]}\n')
                report.write('\n\n')
                changes[verdict_change] = changes.get(verdict_change, 0) + 1

            client.logout()
            report.write(f'\n\nSummary of changes in verdicts (see {filename} for details):')
            report.write(str(changes))
    finally:
        if user is not None:
            user.delete()


def extended_submissions(filename: str) -> None:
    """ Generates a CSV file with all students' submissions extended with some information about
        the user, the problem and the collection """
    subs = Submission.objects.filter(user__is_staff=False, user__is_active=True).order_by('creation_date')
    with open(filename, 'w', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, ['creation_date', 'verdict', 'user', 'first_name', 'last_name',
                                          'problem_id', 'problem_name', 'collection_id', 'collection_name',
                                          'problem_type', ])
        writer.writeheader()
        ptype_cache = {}
        for sub in subs:
            sub_dict = {'creation_date': sub.creation_date,
                        'verdict': sub.verdict_code,
                        'user': sub.user.email,
                        'problem_id': sub.problem.pk,
                        'problem_name': sub.problem.title_md,
                        'collection_id': sub.problem.collection.pk,
                        'collection_name': sub.problem.collection.name_md,
                        'first_name': sub.user.first_name,
                        'last_name': sub.user.last_name,
                        }
            ptype = ptype_cache.get(sub.problem.pk)
            if ptype is None:
                ptype = str(Problem.objects.filter(pk=sub.problem.pk).select_subclasses()[0].problem_type())
            sub_dict['problem_type'] = ptype
            writer.writerow(sub_dict)


def user_submissions_per_type(user) -> dict:
    """ Given a user, returns the number of submission to each type of problem. As the type of
        problem in generated by a subclass method and it is not part of the base Submission,
        we need to traverse manually all user submissions (no possible aggregation) """
    acc = {ptype: 0 for ptype in ProblemType}
    for sub in Submission.objects.filter(user=user):
        prob = Problem.objects.filter(pk=sub.problem.pk).select_subclasses()[0]
        acc[prob.problem_type()] = acc[prob.problem_type()] + 1
    return {str(k): v for k, v in acc.items()}


def submissions_per_user(filename: str) -> None:
    """ Generates a CSV file with a summary of all students' submissions """
    users = get_user_model().objects.filter(is_staff=False, is_active=True)
    dict_list = []
    for user in users:
        user_info = Submission.objects.filter(user=user).aggregate(
            total_envios=Count('pk'),
            envios_AC=Count('pk', filter=Q(verdict_code='AC')),
            envios_TLE=Count('pk', filter=Q(verdict_code='TLE')),
            envios_RE=Count('pk', filter=Q(verdict_code='RE')),
            envios_WA=Count('pk', filter=Q(verdict_code='WA')),
            envios_IE=Count('pk', filter=Q(verdict_code='IE')),
            envios_VE=Count('pk', filter=Q(verdict_code='VE')),
            colecciones_intentadas=Count('problem__collection', distinct=True),
            problemas_intentados=Count('problem', distinct=True),
            problemas_resueltos=Count('problem', distinct=True, filter=Q(verdict_code='AC')),
            inicio_uso=Min('creation_date'),
            fin_uso=Max('creation_date')
        )
        user_info['username'] = user.email
        user_info['first_name'] = user.first_name
        user_info['last_name'] = user.last_name
        user_info.update(user_submissions_per_type(user))
        dict_list.append(user_info)

    with open(filename, 'w', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, dict_list[0].keys())
        writer.writeheader()
        for row in dict_list:
            writer.writerow(row)

#######################################################################################
# Functions for assigning keywords to SQL queries. The list of keywords is the following:
#
#     "projection": projects some columns in the SELECT clause, that is, does not use *
#     "where": has a WHERE clause with some condition
#     "order": performs sorting with ORDER BY
#     "inner_join": performs an inner JOIN
#     "outer_join": performs an outer JOIN, left or right
#     "aggregation": uses aggregation functions: COUNT, MIN, MAX, SUM, AVG
#     "group_by": has a GROUP BY clause
#     "set": uses set operations (UNION, UNION ALL, INTERSECT, INTERSECT ALL, MINUS, MINUS ALL, EXCEPT, EXCEPT ALL)
#     "having": has a HAVING clause
#     "nested": uses a nested query
#     "null": handles null values, either with IS NULL/IS NOT NULL or using functions like COALESCE, NVL, or NVL2
#     "exists": uses the EXISTS operator
#     "like": uses string matching with LIKE
#
#######################################################################################

def is_projection(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query projects some columns in the SELECT clause """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False
    projection = False  # Some SELECT has a list of columns (may be nested)
    for query in statement.find_all(sqlglot.expressions.Select):
        if isinstance(query, sqlglot.expressions.Select):
            if (len(query.expressions) > 1 or
                    (len(query.expressions) == 1 and not isinstance(query.expressions[0], sqlglot.expressions.Star))):
                projection = True

    return projection

def is_where(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query has a WHERE clause with some condition """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    return statement.find(sqlglot.expressions.Where) is not None

def is_order(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query sorts with ORDER BY """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    return statement.find(sqlglot.expressions.Order) is not None

def is_inner_join(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query contains inner joins. CROSS PRODUCTS are considered as inner joins """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    for join in statement.find_all(sqlglot.expressions.Join):
        if join.kind == "INNER" or not join.side:
            return True
    return False

def is_outer_join(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query contains outer joins. CROSS PRODUCTS are considered as inner joins """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    for join in statement.find_all(sqlglot.expressions.Join):
        if join.kind == "OUTER" or join.side:
            return True
    return False

def is_aggregation(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query has aggregation functions: COUNT, MIN, MAX, SUM, AVG """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    return (statement.find(sqlglot.expressions.Count) is not None or
            statement.find(sqlglot.expressions.Min) is not None or
            statement.find(sqlglot.expressions.Max) is not None or
            statement.find(sqlglot.expressions.Sum) is not None or
            statement.find(sqlglot.expressions.Avg) is not None)

def is_group_by(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query has a GROUP BY clause """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    return statement.find(sqlglot.expressions.Group) is not None

def is_set(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL uses set operations:
        UNION, UNION ALL, INTERSECT, INTERSECT ALL, MINUS, MINUS ALL, EXCEPT, EXCEPT ALL
    """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    return (statement.find(sqlglot.expressions.Union) is not None or
            statement.find(sqlglot.expressions.Intersect) is not None or
            statement.find(sqlglot.expressions.Except) is not None)

def is_having(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query has a HAVING clause """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    return statement.find(sqlglot.expressions.Having) is not None

def is_nested(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query has nested queries. We consider WITH queries as nested queries """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False

    for query in statement.find_all(sqlglot.expressions.Select):
        if len(list(query.find_all(sqlglot.expressions.Select))) > 1:
            # find_all returns the whole expression
            return True
    return False

def is_null(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query null values, either by comparing with IS NULL/IS NOT NULL or using functions
        like COALESCE, NVL, or NVL2
    """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False
    return (statement.find(sqlglot.expressions.Coalesce) is not None or
        statement.find(sqlglot.expressions.Null) is not None or
        statement.find(sqlglot.expressions.Nvl2) is not None)

def is_exists(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query contains an EXISTS operator """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False
    return statement.find(sqlglot.expressions.Exists) is not None

def is_like(sql: str, dialect: str = "oracle") -> bool:
    """ Detects if a SQL query a LIKE comparator """
    try:
        statement = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError:
        return False
    return statement.find(sqlglot.expressions.Like) is not None

def keywords(sql: str, dialect: str = "oracle") -> set[str]:
    """ Generates a set of tags that clasify a SQL query """
    checkers = [("projection", is_projection),
                ("where", is_where),
                ("order", is_order),
                ("inner_join", is_inner_join),
                ("outer_join", is_outer_join),
                ("aggregation", is_aggregation),
                ("group_by", is_group_by),
                ("set", is_set),
                ("having", is_having),
                ("nested", is_nested),
                ("null", is_null),
                ("exists", is_exists),
                ("like", is_like)
                ]
    tags = set()
    for (tag, checker) in checkers:
        if checker(sql, dialect):
            tags.add(tag)
    return tags
