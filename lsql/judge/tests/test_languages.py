# -*- coding: utf-8 -*-
"""
Tests for languages
"""
import os

from django.test import TestCase, Client
from django.conf import settings
from django.urls import reverse
from judge.tests.test_views import create_user, create_group, create_collection, create_select_problem
from judge.models import ProcProblem, TriggerProblem
from judge.tests.test_parse import ParseTest
from judge.templatetags import languages_to_flags
from judge.feedback import compare_select_results

class LanguagesTest(TestCase):
    """Tests for the languages"""

    def test_languages_to_flags(self):
        """Test to check if css classes for flags are correctly generated"""
        self.assertIn(languages_to_flags.language_to_flag("en"), "flag-icon-us")
        self.assertIn(languages_to_flags.language_to_flag("es"), "flag-icon-es")

    def test_login_language(self):
        """Test to check if language in login page displays correctly"""
        client = Client()

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:login')
        response = client.get(url, follow=True)
        self.assertIn('Login', response.content.decode('utf-8'))
        self.assertIn('Part of your email that comes before', response.content.decode('utf-8'))
        self.assertIn('Password', response.content.decode('utf-8'))
        self.assertIn('Enter', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:login')
        response = client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Inicio de sesión', response.content.decode('utf-8'))
        self.assertIn('Es la parte de tu e-mail que precede a', response.content.decode('utf-8'))
        self.assertIn('Contraseña', response.content.decode('utf-8'))
        self.assertIn('Entrar', response.content.decode('utf-8'))

    def test_collections_language(self):
        """Test to check if language in collections page displays correctly"""
        client = Client()

        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:collections')
        response = client.get(url, follow=True)
        self.assertIn('Exercises', response.content.decode('utf-8'))
        self.assertIn('My submissions', response.content.decode('utf-8'))
        self.assertIn('Ranking', response.content.decode('utf-8'))
        self.assertIn('Help', response.content.decode('utf-8'))
        self.assertIn('Problem collections', response.content.decode('utf-8'))
        self.assertIn('Name', response.content.decode('utf-8'))
        self.assertIn('Solved', response.content.decode('utf-8'))
        self.assertIn('Total problems', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:collections')
        response = client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ejercicios', response.content.decode('utf-8'))
        self.assertIn('Mis envíos', response.content.decode('utf-8'))
        self.assertIn('Clasificación', response.content.decode('utf-8'))
        self.assertIn('Ayuda', response.content.decode('utf-8'))
        self.assertIn('Colecciones de problemas', response.content.decode('utf-8'))
        self.assertIn('Nombre', response.content.decode('utf-8'))
        self.assertIn('Resueltos', response.content.decode('utf-8'))
        self.assertIn('Total problemas', response.content.decode('utf-8'))

    def test_password_change_language(self):
        """Test to check if language in password change page displays correctly"""
        client = Client()

        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:password_change')
        response = client.get(url, follow=True)
        self.assertIn('Login', response.content.decode('utf-8'))
        self.assertIn('Current password', response.content.decode('utf-8'))
        self.assertIn('New password', response.content.decode('utf-8'))
        self.assertIn('confirmation', response.content.decode('utf-8'))
        self.assertIn('Your password can not be similar to your personal information', response.content.decode('utf-8'))
        self.assertIn('Your password must contain at least 8 characters', response.content.decode('utf-8'))
        self.assertIn('You can not use a common password', response.content.decode('utf-8'))
        self.assertIn('Your password can not be numeric only', response.content.decode('utf-8'))
        self.assertIn('Change password', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:password_change')
        response = client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Inicio de sesión', response.content.decode('utf-8'))
        self.assertIn('Contraseña actual', response.content.decode('utf-8'))
        self.assertIn('Nueva contraseña', response.content.decode('utf-8'))
        self.assertIn('confirmación', response.content.decode('utf-8'))
        self.assertIn('Tu contraseña no puede ser parecida a tu información personal', response.content.decode('utf-8'))
        self.assertIn('Tu contraseña debe contener al menos 8 caracteres', response.content.decode('utf-8'))
        self.assertIn('No puedes usar una contraseña común', response.content.decode('utf-8'))
        self.assertIn('Tu contraseña no puede ser completamente numérica', response.content.decode('utf-8'))
        self.assertIn('Cambiar contraseña', response.content.decode('utf-8'))

    def test_submissions_language(self):
        """Test to check if language in submissions page displays correctly"""
        client = Client()

        create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:submissions')
        response = client.get(url, follow=True)
        self.assertIn('My submissions', response.content.decode('utf-8'))
        self.assertIn('Date', response.content.decode('utf-8'))
        self.assertIn('Problem', response.content.decode('utf-8'))
        self.assertIn('Verdict', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:submissions')
        response = client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Mis envíos', response.content.decode('utf-8'))
        self.assertIn('Fecha', response.content.decode('utf-8'))
        self.assertIn('Problema', response.content.decode('utf-8'))
        self.assertIn('Veredicto', response.content.decode('utf-8'))

    def test_proc_problem_language(self):
        """Test to check if language in proc problem page displays correctly"""
        curr_path = os.path.dirname(__file__)
        client = Client()

        zip_proc_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.PROC_OK)
        collection = create_collection('Colleccion de prueba XYZ')
        user = create_user('5555', 'pepe')
        problem = ProcProblem(zipfile=zip_proc_path, collection=collection, author=user)
        problem.clean()
        problem.save()
        client.login(username='pepe', password='5555')

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:problem', args=[problem.pk])
        response = client.get(url, follow=True)
        self.assertIn('Procedure call', response.content.decode('utf-8'))
        self.assertIn('Expected result', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:problem', args=[problem.pk])
        response = client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Llamada a procedimiento', response.content.decode('utf-8'))
        self.assertIn('Resultado esperado', response.content.decode('utf-8'))

    def test_trigger_problem_language(self):
        """Test to check if language in trigger problem page displays correctly"""
        curr_path = os.path.dirname(__file__)
        client = Client()

        zip_trigger_path = os.path.join(curr_path, ParseTest.ZIP_FOLDER, ParseTest.TRIGGER_OK)
        collection = create_collection('Colleccion de prueba XYZ')
        user = create_user('5555', 'pepe')
        problem = TriggerProblem(zipfile=zip_trigger_path, collection=collection, author=user)
        problem.clean()
        problem.save()
        client.login(username='pepe', password='5555')

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:problem', args=[problem.pk])
        response = client.get(url, follow=True)
        self.assertIn('Executed statements', response.content.decode('utf-8'))
        self.assertIn('Expected result', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:problem', args=[problem.pk])
        response = client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sentencias ejecutadas', response.content.decode('utf-8'))
        self.assertIn('Resultado esperado', response.content.decode('utf-8'))

    def test_feedback_language(self):
        """Test to check language in feedback"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        create_user('5555', 'pedro')
        client.login(username='pedro', password='5555')

        expected = {'header': [['Algo', "<class 'cx_Oracle.NUMBER'>"], ['name', "<class 'cx_Oracle.STRING'>"]],
                    'rows': [[1, 'a'], [2, 'b']]}
        obtained1 = {'header': [['name', "<class 'cx_Oracle.STRING'>"], ['Algo', "<class 'cx_Oracle.NUMBER'>"]],
                     'rows': [['b', 2], ['a', 1]]}
        obtained2 = {'header': [['Algo', "<class 'cx_Oracle.NUMBER'>"], ['name', "<class 'cx_Oracle.STRING'>"],
                                ['name', "<class 'cx_Oracle.STRING'>"]],
                    'rows': [[1, 'a', 'a'], [2, 'b', 'b']]}
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')


        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})

        submit_url_select = reverse('judge:submit', args=[select_problem.pk])
        response = client.post(submit_url_select, {'code': f'{select_problem.solution}; {select_problem.solution}'},
                               follow=True)
        self.assertIn('Exactly expected 1 SQL statement', response.content.decode('utf-8'))

        self.assertIn("Expected: 2 columns", compare_select_results(expected, obtained2, True)[1])
        self.assertIn("Generated by your SQL code: 3 columns", compare_select_results(expected, obtained2, True)[1])
        self.assertIn("Number of columns obtained:", compare_select_results(expected, obtained2, True)[1])

        self.assertIn("name of the 1ª column", compare_select_results(expected, obtained1, False)[1])
        self.assertIn("Expected name: Algo", compare_select_results(expected, obtained1, False)[1])
        self.assertIn("Generated name by your SQL code: name",
                      compare_select_results(expected, obtained1, False)[1])


        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})

        submit_url_select = reverse('judge:submit', args=[select_problem.pk])
        response = client.post(submit_url_select, {'code': f'{select_problem.solution}; {select_problem.solution}'},
                               follow=True)
        self.assertIn('Se esperaba exactamente 1 sentencia SQL', response.content.decode('utf-8'))

        self.assertIn("Esperado: 2 columnas", compare_select_results(expected, obtained2, True)[1])
        self.assertIn("Generado por tu código SQL: 3 columnas", compare_select_results(expected, obtained2, True)[1])
        self.assertIn("Número de columnas obtenidas:", compare_select_results(expected, obtained2, True)[1])

        self.assertIn("nombre de la 1ª columna", compare_select_results(expected, obtained1, False)[1])
        self.assertIn("Nombre esperado: Algo", compare_select_results(expected, obtained1, False)[1])
        self.assertIn("Nombre generado por tu código SQL: name",
                      compare_select_results(expected, obtained1, False)[1])

    def test_language_selector(self):
        """Test to check language selector"""
        client = Client()
        create_user('5555', 'pedro')
        client.login(username='pedro', password='5555')

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        url = reverse('judge:collections')
        response = client.get(url, follow=True)
        self.assertIn('flag-icon-us', response.content.decode('utf-8'))
        self.assertNotIn('flag-icon-es', response.content.decode('utf-8'))
        self.assertIn('value="en" selected', response.content.decode('utf-8'))
        self.assertNotIn('value="es" selected', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        url = reverse('judge:collections')
        response = client.get(url, follow=True)
        self.assertIn('flag-icon-es', response.content.decode('utf-8'))
        self.assertNotIn('flag-icon-us', response.content.decode('utf-8'))
        self.assertIn('value="es" selected', response.content.decode('utf-8'))
        self.assertNotIn('value="en" selected', response.content.decode('utf-8'))

    def test_ranking_language(self):
        """Test to check ranking language page"""
        client = Client()
        collection = create_collection('Colleccion de prueba XYZ')
        user = create_user('5555', 'pepe')
        client.login(username='pepe', password='5555')
        group_a = create_group('1A')
        group_a.user_set.add(user)

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'en'})
        ranking_url = reverse('judge:result', args=[collection.pk])
        response = client.get(ranking_url, follow=True)

        self.assertIn('Group', response.content.decode('utf-8'))
        self.assertIn('User', response.content.decode('utf-8'))
        self.assertIn('Score', response.content.decode('utf-8'))
        self.assertIn('LEGEND', response.content.decode('utf-8'))
        self.assertIn('Solved', response.content.decode('utf-8'))
        self.assertIn('Sum of the first accepted submission of each exercise', response.content.decode('utf-8'))

        client.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'es'})
        ranking_url = reverse('judge:result', args=[collection.pk])
        response = client.get(ranking_url, follow=True)

        self.assertIn('Grupo', response.content.decode('utf-8'))
        self.assertIn('Usuario', response.content.decode('utf-8'))
        self.assertIn('Puntuación', response.content.decode('utf-8'))
        self.assertIn('LEYENDA', response.content.decode('utf-8'))
        self.assertIn('Resueltos', response.content.decode('utf-8'))
        self.assertIn('Suma del primer envío aceptado de cada ejercicio', response.content.decode('utf-8'))
