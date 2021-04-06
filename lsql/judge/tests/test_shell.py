# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the shell module
"""

import os

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from judge.models import SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem, Collection, Problem
from judge.shell import create_users_from_csv, adapt_db_result_to_list


class ShellTest(TestCase):
    """Tests for module parse"""
    FILE_FOLDER = 'csv_files'
    CSV_OK_TEST = 'test_ok.csv'
    CSV_EMPTY_FIELDS = ['csv_empty_document.csv', 'csv_empty_first.csv', 'csv_empty_name.csv', 'csv_empty_email.csv',
                        'csv_empty_last.csv']

    def test_valid_csv(self):
        """Valid CSV file with 3 users"""
        # Delete existing users and groups
        Group.objects.all().delete()
        get_user_model().objects.all().delete()

        group_name = 'Clase ABC curso X/Y'
        curr_path = os.path.dirname(__file__)
        path = os.path.join(curr_path, self.FILE_FOLDER, self.CSV_OK_TEST)
        create_users_from_csv(path, group_name)

        # The new group has 3 memebers
        new_group = Group.objects.filter(name=group_name)[0]
        self.assertEqual(len(new_group.user_set.all()), 3)

        juan = get_user_model().objects.get(username='juan')
        self.assertTrue(juan.check_password('11111111X'))
        self.assertFalse(juan.check_password('11113111X'))
        self.assertEqual(juan.first_name, 'Juan')
        self.assertEqual(len(juan.groups.all()), 1)
        self.assertEqual(juan.groups.all()[0], new_group)

        eva = get_user_model().objects.get(username='eva')
        self.assertTrue(eva.check_password('22222222X'))
        self.assertFalse(eva.check_password('11113111X'))
        self.assertEqual(eva.first_name, 'EVA MARIA')
        self.assertEqual(eva.last_name, 'MARTIN KEPLER')
        self.assertEqual(len(eva.groups.all()), 1)
        self.assertEqual(eva.groups.all()[0], new_group)

        froilan = get_user_model().objects.get(username='froilan')
        self.assertTrue(froilan.check_password('33333333X'))
        self.assertFalse(froilan.check_password('11113111X'))
        self.assertEqual(froilan.first_name, 'JUAN FROILAN DE TODOS LOS SANTOS DE JESÚS')
        self.assertEqual(froilan.last_name, 'KUPU KUPI')
        self.assertEqual(len(froilan.groups.all()), 1)
        self.assertEqual(froilan.groups.all()[0], new_group)

    def test_empty_fields(self):
        """CSV files where some fields are empty"""
        curr_path = os.path.dirname(__file__)
        for filename in self.CSV_EMPTY_FIELDS:
            # Delete existing users and groups
            get_user_model().objects.all().delete()
            Group.objects.all().delete()
            path = os.path.join(curr_path, self.FILE_FOLDER, filename)
            with self.assertRaises(AssertionError):
                create_users_from_csv(path, f"Test-{filename}")

    def test_adapt_db_expected_list(self):
        """Test for adapting dictionaries in initial_db and expected_result to unitary lists """
        collection = Collection(name_md='Colección', position=8, description_md='Colección de pruebas', author=None)
        collection.save()

        # Problems with dictionaries or already with [dict]
        problems = [
            SelectProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                          author=None, expected_result=dict()),
            DMLProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                       author=None, expected_result=dict()),
            FunctionProblem(title_html="titulo", text_html="enunciado", initial_db=dict(),
                            collection=collection, author=None, expected_result=dict()),
            ProcProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                        author=None, expected_result=dict()),
            TriggerProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                           author=None, expected_result=dict()),
            SelectProblem(title_html="titulo", text_html="enunciado", initial_db=[dict()], collection=collection,
                          author=None, expected_result=[dict()]),  # already has the right representation
        ]

        for prob in problems:
            prob.save()

        adapt_db_result_to_list()
        for prob in Problem.objects.all().select_subclasses():
            self.assertIs(type(prob.initial_db), list)
            self.assertIs(type(prob.initial_db[0]), dict)
            self.assertIs(type(prob.expected_result), list)
            self.assertIs(type(prob.expected_result[0]), dict)

        for prob in Problem.objects.all():
            prob.delete()

        # Problems with wrong types in initial_db or expected_result
        wrong_problems = [
            SelectProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                          author=None, expected_result=3),
            DMLProblem(title_html="titulo", text_html="enunciado", initial_db=6, collection=collection,
                       author=None, expected_result=dict()),
            FunctionProblem(title_html="titulo", text_html="enunciado", initial_db=[],
                            collection=collection, author=None, expected_result=dict()),
            ProcProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                        author=None, expected_result=[3]),
            TriggerProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                           author=None, expected_result=[]),
            TriggerProblem(title_html="titulo", text_html="enunciado", initial_db=dict(), collection=collection,
                           author=None, expected_result=[dict(), dict(), False]),
        ]

        # Tries every wrong program individually (removing it after checking the exception)
        for prob in wrong_problems:
            prob.save()
            with self.assertRaises(TypeError):
                adapt_db_result_to_list()
            prob.delete()
