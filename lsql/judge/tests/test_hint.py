# -*- coding: utf-8 -*-
"""
Tests for hints
"""
from datetime import datetime
import os

from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from judge.types import VeredictCode
from judge.tests.test_views import create_user, create_collection, create_select_problem, create_submission
from judge.models import SelectProblem, DMLProblem, FunctionProblem, \
    ProcProblem, TriggerProblem, DiscriminantProblem, Submission, Hint, UsedHint


def create_hint(problem, id_hint, num):
    """ Creates and stores a Hint of a Problem """
    description = f'descripcion de la pista {id_hint}'
    hint = Hint(text_md=description, problem=problem, num_submit=num)
    hint.save()
    return hint


def create_used_hint(hint, user):
    """ Creates and stores a used Hint of a Problem """
    used_hint = UsedHint(user=user, request_date=datetime(2020, 3, 5), hint_definition=hint)
    used_hint.save()
    return used_hint


class HintTest(TestCase):
    """Tests for the hints and used hints"""
    ZIP_FOLDER = 'zip_files'
    SELECT_HINTS = 'select_with_hints.zip'
    SELECT_HINTS_PRO = 'select_with_hints_pro.zip'
    DML_HINTS = 'dml_with_hints.zip'
    FUNCTION_HINTS = 'function_with_hints.zip'
    PROC_HINTS = 'proc_with_hints.zip'
    TRIGGER_HINTS = 'trigger_with_hints.zip'
    DISCRIMINANT_HINTS = 'discriminant_with_hints.zip'
    SELECT_HINTS_WRONG_DESCRIPTION = 'select_wrong_description_hint.zip'
    SELECT_HINTS_WRONG_DESCRIPTION2 = 'select_wrong_description_hint2.zip'
    SELECT_HINTS_WRONG_SUBMITS = 'select_wrong_num_sub_hint.zip'
    SELECT_HINTS_WRONG_SUBMITS2 = 'select_wrong_num_sub_hint2.zip'

    def test_give_hint(self):
        """check the correct operation of the hints"""
        client = Client()
        user = create_user('2222', 'tamara')
        collection = create_collection('Colleccion de prueba TTT')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')

        description1 = '<div class="d-flex p-2">\n    ' \
                       '<div class="bg-success h-40 w-25 text-center mb-1 border border-dark text-white ' \
                       'justify-content-center align-self-center ">\n' \
                       '        Pista 1\n    </div>\n    <div class="text-center w-75">\n        ' \
                       'descripcion de la pista 1\n    </div>\n</div>'
        description2 = '<div class="d-flex p-2">\n    ' \
                       '<div class="bg-success h-40 w-25 text-center mb-1 border border-dark text-white ' \
                       'justify-content-center align-self-center ">\n' \
                       '        Pista 2\n    </div>\n    <div class="text-center w-75">\n        ' \
                       'descripcion de la pista 2\n    </div>\n</div>'
        create_hint(problem, 1, 3)
        hint2 = create_hint(problem, 2, 5)
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        create_submission(problem, user, VeredictCode.WA, 'select *** from')

        hint_url = reverse('judge:hint', args=[problem.pk])
        client.login(username='tamara', password='2222')

        # JSON with the first hint
        response = client.post(hint_url, follow=True)
        self.assertEqual(response.json()['hint'], description1)

        # JSON with the message that the next hint is not available
        num_error = Submission.objects.filter(problem=problem, user=user).count()
        num = hint2.num_submit - num_error
        msg = f'Número de envíos que faltan para obtener la siguiente pista: {num}.'
        response = client.post(hint_url, follow=True)
        self.assertEqual(response.json()['hint'], '')
        self.assertEqual(response.json()['msg'], msg)
        self.assertEqual(response.json()['more_hints'], True)

        # JSON with the last hint
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        mens = 'No hay más pistas disponibles para este ejercicio.'
        response = client.post(hint_url, follow=True)
        self.assertEqual(response.json()['hint'], description2)
        self.assertEqual(response.json()['msg'], mens)
        self.assertEqual(response.json()['more_hints'], False)

        # JSON if the problem don't have any hint
        problem_3 = create_select_problem(collection, 'SelectProblem 3 DEF ABC')
        hint_url_3 = reverse('judge:hint', args=[problem_3.pk])
        client.post(hint_url_3, follow=False)
        self.assertEqual(response.json()['more_hints'], False)

        # Markdown to HTML
        hint_md = create_hint(problem, 3, 3)
        self.assertEqual(hint_md.get_text_html(), 'descripcion de la pista 3')

    def test_same_hints(self):
        """Test when the user use all available hints"""
        client = Client()
        user = create_user('2222', 'tamara')
        collection = create_collection('Colleccion de prueba TTT')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        hint1 = create_hint(problem, 1, 3)
        hint2 = create_hint(problem, 2, 5)
        create_used_hint(hint1, user)
        create_used_hint(hint2, user)
        client.login(username='tamara', password='2222')
        msg = 'No hay más pistas disponibles para este ejercicio.'
        hint_url = reverse('judge:hint', args=[problem.pk])
        response = client.post(hint_url, follow=True)
        self.assertEqual(response.json()['msg'], msg)

    def test_hint_used(self):
        """Test to check the text of the used hints"""
        client = Client()
        user = create_user('2222', 'tamara')
        collection = create_collection('Colleccion de prueba TTT')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        client.login(username='tamara', password='2222')
        hint = create_hint(problem, 1, 1)
        create_used_hint(hint, user)
        problem_url = reverse('judge:problem', args=[problem.pk])
        response = client.get(problem_url, follow=True)
        self.assertIn(hint.text_md, response.content.decode('utf-8'))

    def test_show_hints(self):
        """Test to check the table of used hints of a user"""
        client = Client()
        user = create_user('2222', 'tamara')
        collection = create_collection('Colleccion de prueba TTT')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        problem_3 = create_select_problem(collection, 'SelectProblem 3 DEF ABC')
        client.login(username='tamara', password='2222')
        hint = create_hint(problem, 1, 1)
        hint2 = create_hint(problem, 2, 1)
        hint3 = create_hint(problem_3, 3, 1)

        # The table is empty, the user has no used hint
        table_hint_url = reverse('judge:hints')
        response = client.get(table_hint_url, follow=True)
        self.assertIn(user.username, response.content.decode('utf-8'))
        self.assertNotIn('SelectProblem', response.content.decode('utf-8'))

        # The table contains the first hint used for first problem
        create_used_hint(hint, user)
        table_hint_url = reverse('judge:hints')
        response = client.get(table_hint_url, follow=True)
        self.assertIn(user.username, response.content.decode('utf-8'))
        self.assertIn('SelectProblem ABC DEF', response.content.decode('utf-8'))
        self.assertIn(hint.text_md, response.content.decode('utf-8'))
        self.assertNotIn(hint2.text_md, response.content.decode('utf-8'))
        self.assertNotIn('SelectProblem 3 ABC DEF', response.content.decode('utf-8'))
        self.assertNotIn(hint3.text_md, response.content.decode('utf-8'))

        # The table contains the second hint used for first problem
        create_used_hint(hint2, user)
        table_hint_url2 = reverse('judge:hints')
        response = client.get(table_hint_url2, follow=True)
        self.assertIn(user.username, response.content.decode('utf-8'))
        self.assertIn('SelectProblem ABC DEF', response.content.decode('utf-8'))
        self.assertIn(hint.text_md, response.content.decode('utf-8'))
        self.assertIn(hint2.text_md, response.content.decode('utf-8'))
        self.assertNotIn('SelectProblem 3 DEF ABC', response.content.decode('utf-8'))
        self.assertNotIn(hint3.text_md, response.content.decode('utf-8'))

        # The table contains the first hint used for second problem
        create_used_hint(hint3, user)
        table_hint_url3 = reverse('judge:hints')
        response = client.get(table_hint_url3, follow=True)
        self.assertIn(user.username, response.content.decode('utf-8'))
        self.assertIn('SelectProblem ABC DEF', response.content.decode('utf-8'))
        self.assertIn(hint.text_md, response.content.decode('utf-8'))
        self.assertIn(hint2.text_md, response.content.decode('utf-8'))
        self.assertIn('SelectProblem 3 DEF ABC', response.content.decode('utf-8'))
        self.assertIn(hint3.text_md, response.content.decode('utf-8'))

    def test_load_hint(self):
        """Test to check if hints.md is loaded correctly"""
        curr_path = os.path.dirname(__file__)
        zip_dml_path = os.path.join(curr_path, self.ZIP_FOLDER, self.DML_HINTS)
        zip_function_path = os.path.join(curr_path, self.ZIP_FOLDER, self.FUNCTION_HINTS)
        zip_proc_path = os.path.join(curr_path, self.ZIP_FOLDER, self.PROC_HINTS)
        zip_trigger_path = os.path.join(curr_path, self.ZIP_FOLDER, self.TRIGGER_HINTS)
        zip_discriminant_path = os.path.join(curr_path, self.ZIP_FOLDER, self.DISCRIMINANT_HINTS)
        collection = create_collection('Coleccion 1')

        dml = DMLProblem(zipfile=zip_dml_path, collection=collection)
        function = FunctionProblem(zipfile=zip_function_path, collection=collection)
        proc = ProcProblem(zipfile=zip_proc_path, collection=collection)
        trigger = TriggerProblem(zipfile=zip_trigger_path, collection=collection)
        discriminant = DiscriminantProblem(zipfile=zip_discriminant_path, collection=collection)

        hints_expected1 = (3, 'descripcion pista 1')
        hints_expected2 = (5, 'descripcion pista 2')
        hints_expected3 = (10, 'descripcion pista 3')

        for problem in [dml, function, proc, trigger, discriminant]:
            problem.clean()
            problem.save()
            hints = Hint.objects.filter(problem=problem).order_by('num_submit')
            self.assertEqual(hints.count(), 3)
            self.assertEqual(hints_expected1[0], hints[0].num_submit)
            self.assertEqual(hints_expected1[1], hints[0].text_md)
            self.assertEqual(hints_expected2[0], hints[1].num_submit)
            self.assertEqual(hints_expected2[1], hints[1].text_md)
            self.assertEqual(hints_expected3[0], hints[2].num_submit)
            self.assertEqual(hints_expected3[1], hints[2].text_md)

    def test_long_hint(self):
        """Test to check if hints.md is loaded correctly to a SelectProblem.
        It checks both hints with one line and hints with several lines"""
        curr_path = os.path.dirname(__file__)
        zip_select_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_HINTS)
        zip_select_pro_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_HINTS_PRO)
        collection = create_collection('Coleccion 1')
        select = SelectProblem(zipfile=zip_select_path, collection=collection)
        select_pro = SelectProblem(zipfile=zip_select_pro_path, collection=collection)

        hints_expected1 = (3, 'descripcion pista 1')
        hints_expected2 = (5, 'descripcion pista 2')
        hints_expected3 = (10, 'descripcion pista 3')
        text_md = """Ten en **cuenta** que:
 * debes seleccionar las tablas
 * debes elegir cuidadosamente las columnas"""
        hits_expected_pro = (5, text_md)

        # Check hints loaded for SelectProblem
        select.clean()
        select.save()
        hints = Hint.objects.filter(problem=select).order_by('num_submit')
        self.assertEqual(hints.count(), 3)
        self.assertEqual(hints_expected1[0], hints[0].num_submit)
        self.assertEqual(hints_expected1[1], hints[0].text_md)
        self.assertEqual(hints_expected2[0], hints[1].num_submit)
        self.assertEqual(hints_expected2[1], hints[1].text_md)
        self.assertEqual(hints_expected3[0], hints[2].num_submit)
        self.assertEqual(hints_expected3[1], hints[2].text_md)

        # Check hints loaded for SelectProblem pro
        select_pro.clean()
        select_pro.save()
        hints = Hint.objects.filter(problem=select_pro).order_by('num_submit')
        self.assertEqual(hints.count(), 3)
        self.assertEqual(hints_expected1[0], hints[0].num_submit)
        self.assertEqual(hints_expected1[1], hints[0].text_md)
        self.assertEqual(hits_expected_pro[0], hints[1].num_submit)
        self.assertEqual(hits_expected_pro[1], hints[1].text_md)
        self.assertEqual(hints_expected3[0], hints[2].num_submit)
        self.assertEqual(hints_expected3[1], hints[2].text_md)

    def test_with_wrong_zips(self):
        """Test to check that ZIP files with wrong hints.md file raise ValidationError"""
        curr_path = os.path.dirname(__file__)
        zip_select_description_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_HINTS_WRONG_DESCRIPTION)
        zip_select_description2_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_HINTS_WRONG_DESCRIPTION2)
        zip_select_sub_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_HINTS_WRONG_SUBMITS)
        zip_select_sub2_path = os.path.join(curr_path, self.ZIP_FOLDER, self.SELECT_HINTS_WRONG_SUBMITS2)

        select_description = SelectProblem(zipfile=zip_select_description_path)
        select_description2 = SelectProblem(zipfile=zip_select_description2_path)
        select_sub = SelectProblem(zipfile=zip_select_sub_path)
        select_sub2 = SelectProblem(zipfile=zip_select_sub2_path)

        for problem in [select_description, select_sub, select_sub2, select_description2]:
            self.assertRaises(ValidationError, problem.clean)
