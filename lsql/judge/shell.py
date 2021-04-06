# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Methods for batch processing that can be invoked from the shell (python manage.py shell).
For example: create a group of users from a CSV list of students
"""

import csv

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Problem


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
