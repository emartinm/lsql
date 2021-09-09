# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

More Unit tests checking views behavior
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group

from judge.tests.test_common import create_superuser, create_user, create_collection, create_select_problem


class ViewsTest2(TestCase):
    """Tests for the module views"""

    def test_visibility(self):
        """ Collections are properly shown and accessed depending on visibility and user role """
        user_staff = create_superuser('0000', username='staff')
        create_user('5555', 'pepe')
        visible_col = create_collection('Visible collection', visibility=True, author=user_staff)
        hidden_col = create_collection('Not visible collection', visibility=False, author=user_staff)
        hidden_problem = create_select_problem(hidden_col, 'Hidden problem')

        collections_url = reverse('judge:collections')
        visible_col_url = reverse('judge:collection', args=[visible_col.pk])
        hidden_col_url = reverse('judge:collection', args=[hidden_col.pk])
        hidden_problem_url = reverse('judge:problem', args=[hidden_problem.pk])
        ranking_url = reverse('judge:results')
        visible_ranking_url = reverse('judge:result', args=[visible_col.pk])
        hidden_ranking_url = reverse('judge:result', args=[hidden_col.pk])
        client = Client()

        # Visibility checks for students
        client.login(username='pepe', password='5555')
        response = client.get(collections_url, follow=True)
        self.assertIn(visible_col.name_html, response.content.decode('utf-8'))
        self.assertNotIn(hidden_col.name_html, response.content.decode('utf-8'))
        response = client.get(ranking_url, follow=True)
        self.assertIn(visible_col.name_html, response.content.decode('utf-8'))
        self.assertNotIn(hidden_col.name_html, response.content.decode('utf-8'))

        response = client.get(visible_col_url, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(hidden_col_url, follow=True)
        self.assertEqual(response.status_code, 403)
        response = client.get(hidden_problem_url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(client.get(visible_ranking_url, follow=True).status_code, 200)
        self.assertEqual(client.get(hidden_ranking_url, follow=True).status_code, 403)
        client.logout()

        # Visibility checks for teachers
        client.login(username='staff', password='0000')
        response = client.get(collections_url, follow=True)
        self.assertIn(visible_col.name_html, response.content.decode('utf-8'))
        self.assertIn(hidden_col.name_html, response.content.decode('utf-8'))
        response = client.get(ranking_url, follow=True)
        self.assertIn(visible_col.name_html, response.content.decode('utf-8'))
        self.assertIn(hidden_col.name_html, response.content.decode('utf-8'))

        response = client.get(visible_col_url, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(hidden_col_url, follow=True)
        self.assertEqual(response.status_code, 200)
        response = client.get(hidden_problem_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get(visible_ranking_url, follow=True).status_code, 200)
        self.assertEqual(client.get(hidden_ranking_url, follow=True).status_code, 200)
        client.logout()

    def test_visibility_group(self):
        """ Collections are properly shown when filtered by groups """
        profe1 = create_superuser('0000', username='profe1')
        profe2 = create_superuser('0000', username='profe2')
        create_user('0000', 'pepe')
        group1 = Group.objects.create(name='g1')
        group2 = Group.objects.create(name='g2')
        group1.user_set.add(profe1)
        group2.user_set.add(profe1)
        group2.user_set.add(profe2)

        col1 = create_collection('Col1', visibility=True, author=profe1)
        col2 = create_collection('Col2', visibility=False, author=profe1)
        col3 = create_collection('Col3', visibility=True, author=profe2)

        collections_url = reverse('judge:collections')
        client = Client()

        # Teachers can view all collections from authors in the group
        client.login(username='profe1', password='0000')

        response = client.get(collections_url + '?group=500', follow=True)  # Group does not exist
        self.assertEqual(response.status_code, 404)

        response = client.get(collections_url + '?group=dolphin', follow=True)  # Invalid group
        self.assertEqual(response.status_code, 404)

        response = client.get(collections_url + f'?group={group1.pk}', follow=True)
        self.assertIn(col1.name_html, response.content.decode('utf-8'))
        self.assertIn(col2.name_html, response.content.decode('utf-8'))
        self.assertNotIn(col3.name_html, response.content.decode('utf-8'))

        response = client.get(collections_url + f'?group={group2.pk}', follow=True)
        self.assertIn(col1.name_html, response.content.decode('utf-8'))
        self.assertIn(col2.name_html, response.content.decode('utf-8'))
        self.assertIn(col3.name_html, response.content.decode('utf-8'))
        client.logout()

        # Students can only view visible collections from authors in the group
        client.login(username='pepe', password='0000')
        response = client.get(collections_url + f'?group={group1.pk}', follow=True)
        self.assertIn(col1.name_html, response.content.decode('utf-8'))
        self.assertNotIn(col2.name_html, response.content.decode('utf-8'))
        self.assertNotIn(col3.name_html, response.content.decode('utf-8'))

        response = client.get(collections_url + f'?group={group2.pk}', follow=True)
        self.assertIn(col1.name_html, response.content.decode('utf-8'))
        self.assertNotIn(col2.name_html, response.content.decode('utf-8'))
        self.assertIn(col3.name_html, response.content.decode('utf-8'))
        client.logout()
