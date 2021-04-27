# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Methods for batch processing that can be invoked from the shell (python manage.py shell).
For example: create a group of users from a CSV list of students
"""

import csv
import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.conf import settings

from .models import Problem, Submission


def create_users_from_csv(csv_filename: str, group_name: str):
    """
    Batch creation of users from a CSV file, each line representing a new user. The username is the
    first part of the email (before @) and the password is the document number. Assigns every new
    user to a new created group with name 'group_name'

    Each line has the following fields:
      FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,MAT.,CONV.,OBSERVACIÓN,CORREO,TELÉFONO
    """
    group = Group.objects.create(name=group_name)
    with open(csv_filename, encoding='utf_8') as csvfile:
        reader = csv.DictReader(csvfile)
        create_users_from_list(reader, group)


def create_users_from_list(dict_list, group: Group):
    """
    Batch creation of users from a list of dictionaries, each dictionary representing a new user. The username is the
    first part of the email (before @) and the password is the document number.

    Dictionaries have the following keys:
      FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,MAT.,CONV.,OBSERVACIÓN,CORREO,TELÉFONO
    """
    assert group  # Group is set
    for user_dict in dict_list:
        email = user_dict['CORREO']
        username = email.split('@')[0]
        password = user_dict['DOCUMENTO']
        first_name = user_dict['NOMBRE COMPLETO'].split(',')[1].strip()
        last_name = user_dict['NOMBRE COMPLETO'].split(',')[0].strip()

        # Safety checks
        assert username
        assert password
        assert first_name
        assert last_name

        user = get_user_model().objects.create_user(username, email, password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        group.user_set.add(user)
        print(f'Saved User("{username}", "{email}", "{password}", "{first_name}", "{last_name}") in group "{group}"')


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


def rejudge(verdict_code, filename='rejudge.txt', tests=False, start=datetime.datetime(1970, 1, 1),
            end=datetime.datetime.now()):
    """ Judges again all the submission in the period [start, end] with some verdict_code. For each submission,
        submit the code, compares the veredict, and stores detailed information in the 'filename'.
        Use tests=False for Django tests, tests=True for normal use
    """
    username = 'rejudge_user_test_983'
    passwd = '1111'

    try:
        subs = Submission.objects.filter(veredict_code=verdict_code, creation_date__gte=start, creation_date__lte=end)
        rejudge_users = get_user_model().objects.filter(username=username)
        # In case the user was not deleted in a previous execution
        user = (rejudge_users[0] if len(rejudge_users) == 1 else
                get_user_model().objects.create_user(username=username, password=passwd))
        client = Client()
        client.login(username=username, password=passwd)

        changes = dict()
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
                verdict_change = f'{sub.veredict_code} --> {response_json["veredict"]}'
                report.write(f'Verdict: {verdict_change}\n')
                report.write(f'New feedback: {response_json["feedback"]}\n')
                report.write('\n\n')
                changes[verdict_change] = changes.get(verdict_change, 0) + 1

            client.logout()
            report.write(f'\n\nSummary of changes in verdicts (see {filename} for details):')
            report.write(str(changes))
    finally:
        user.delete()
