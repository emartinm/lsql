# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Methods for batch processing that can be invoked from the shell (python manage.py shell).
For example: create a group of users from a CSV list of students
"""

import csv
from django.contrib.auth import get_user_model


def create_users_from_csv(csv_filename):
    """
    Batch creation of users from a CSV file, each line representing a new user. The username is the
    first part of the email (before @) and the password is the document number.

    Each line has the following fields:
      FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,MAT.,CONV.,OBSERVACIÓN,CORREO,TELÉFONO
    """
    with open(csv_filename, encoding='utf_8') as csvfile:
        reader = csv.DictReader(csvfile)
        create_users_from_list(reader)


def create_users_from_list(dict_list):
    """
    Batch creation of users from a list of dictionaries, each dictionary representing a new user. The username is the
    first part of the email (before @) and the password is the document number.

    Dictionaries have the following keys:
      FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,MAT.,CONV.,OBSERVACIÓN,CORREO,TELÉFONO
    """
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
        print(f'Saved User("{username}", "{email}", "{password}", "{first_name}", "{last_name}")')
