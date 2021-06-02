# -*- coding: utf-8 -*-
"""
Tests for hints
"""
from datetime import datetime

from django.test import TestCase, Client
from django.urls import reverse

from judge.models import Submission, Hint, UsedHint
from judge.types import VeredictCode
from judge.tests.test_views import create_user, create_collection, create_select_problem, create_submission


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
