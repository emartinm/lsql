# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the shell module
"""

import os

from django.test import TestCase
from django.contrib.auth import get_user_model

from judge.shell import create_users_from_csv


class ShellTest(TestCase):
    """Tests for module parse"""
    FILE_FOLDER = 'csv_files'
    CSV_OK_TEST = 'test_ok.csv'
    CSV_EMPTY_FIELDS = ['csv_empty_document.csv', 'csv_empty_first.csv', 'csv_empty_name.csv', 'csv_empty_email.csv',
                        'csv_empty_last.csv']

    def test_valid_csv(self):
        """Valid CSV file with 3 users"""
        for username in ['juan', 'eva', 'froilan']:
            with self.assertRaises(get_user_model().DoesNotExist):
                get_user_model().objects.get(username=username)

        curr_path = os.path.dirname(__file__)
        path = os.path.join(curr_path, self.FILE_FOLDER, self.CSV_OK_TEST)
        create_users_from_csv(path)

        juan = get_user_model().objects.get(username='juan')
        self.assertTrue(juan.check_password('11111111X'))
        self.assertFalse(juan.check_password('11113111X'))
        self.assertTrue(juan.first_name == 'Juan')

        eva = get_user_model().objects.get(username='eva')
        self.assertTrue(eva.check_password('22222222X'))
        self.assertFalse(eva.check_password('11113111X'))
        self.assertTrue(eva.first_name == 'EVA MARIA')
        self.assertTrue(eva.last_name == 'MARTIN KEPLER')

        froilan = get_user_model().objects.get(username='froilan')
        self.assertTrue(froilan.check_password('33333333X'))
        self.assertFalse(froilan.check_password('11113111X'))
        self.assertTrue(froilan.first_name == 'JUAN FROILAN DE TODOS LOS SANTOS DE JESÚS')
        self.assertTrue(froilan.last_name == 'KUPU KUPI')

    def test_empty_fields(self):
        """CSV files where some fields are empty"""
        curr_path = os.path.dirname(__file__)
        for filename in self.CSV_EMPTY_FIELDS:
            path = os.path.join(curr_path, self.FILE_FOLDER, filename)
            with self.assertRaises(AssertionError):
                create_users_from_csv(path)
