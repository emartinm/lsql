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


def create_hint(problem, name, num):
    """ Creates and stores a Hint of a Problem """
    description = 'descripcion de la pista 1'
    hint = Hint(name_md=name, description_md=description, problem=problem, num_submit=num)
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
        hint1 = create_hint(problem, 'pista1', 3)
        hint2 = create_hint(problem, 'pista2', 5)
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        create_submission(problem, user, VeredictCode.WA, 'select *** from')

        hint_url = reverse('judge:hint', args=[problem.pk])
        client.login(username='tamara', password='2222')

        # JSON with the first hint
        response = client.post(hint_url, {'pista': [hint1.name_html, hint1.description_html]}, follow=True)
        self.assertIn(response.json()['pista'][1], hint1.description_html)

        # JSON with the message that the next hint is not available
        num_error = Submission.objects.filter(problem=problem, user=user).count()
        num = hint2.num_submit - num_error
        msg = f'Número de envíos que faltan para obtener la siguiente pista: {num}.'
        response = client.get(hint_url, {'msg': msg}, follow=True)
        self.assertEqual(response.json()['msg'], msg)

        # JSON with the last hint
        create_submission(problem, user, VeredictCode.WA, 'select *** from')
        mens = 'No hay más pistas disponibles para este ejercicio.'
        response = client.post(hint_url, {'msg': mens}, follow=True)
        self.assertEqual(response.json()['msg'], mens)

        # JSON if the problem don't have any hint
        problem_3 = create_select_problem(collection, 'SelectProblem 3 DEF ABC')
        hint_url_3 = reverse('judge:hint', args=[problem_3.pk])
        client.post(hint_url_3, follow=False)

    def test_same_hints(self):
        """Test when the user use all available hints"""
        client = Client()
        user = create_user('2222', 'tamara')
        collection = create_collection('Colleccion de prueba TTT')
        problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        hint1 = create_hint(problem, 'pista1', 3)
        hint2 = create_hint(problem, 'pista2', 5)
        create_used_hint(hint1, user)
        create_used_hint(hint2, user)
        client.login(username='tamara', password='2222')
        msg = 'No hay más pistas disponibles para este ejercicio.'
        hint_url = reverse('judge:hint', args=[problem.pk])
        response = client.get(hint_url, {'msg': msg}, follow=True)
        self.assertEqual(response.json()['msg'], msg)
