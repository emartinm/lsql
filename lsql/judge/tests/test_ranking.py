# -*- coding: utf-8 -*-
"""
Tests for rankings
"""
from datetime import datetime

import tempfile
import openpyxl
from django.test import TestCase, Client
from django.urls import reverse
from judge.models import Submission
from judge.types import VeredictCode
from judge.tests.test_views import create_user, create_superuser, create_group, create_collection, create_select_problem
from judge.views import first_day_of_course

class RankingTest(TestCase):
    """Tests for the module of rankings"""
    def test_download_ranking(self):
        """ Test to download excel of results """
        client = Client()
        user = create_user('2222', 'tamara')
        teacher = create_superuser('1111', 'teacher')
        group_a = create_group('1A')
        group_a.user_set.add(user)
        start = first_day_of_course(datetime(2020, 9, 1))
        end = datetime(2021, 3, 7).strftime('%Y-%m-%d')
        collection = create_collection('Coleccion 1')
        select_problem = create_select_problem(collection, 'SelectProblem ABC DEF')
        sub = Submission.objects.create(code='SELECT * FROM test where n = 1000',
                                        user=user, veredict_code=VeredictCode.WA, problem=select_problem)
        sub.save()
        Submission.objects.filter(id=sub.id).update(creation_date=datetime(2021, 3, 5))
        client.login(username=teacher.username, password='1111')
        url = reverse('judge:download_ranking', args=[collection.pk])
        response = client.get(url, {'group': group_a.id, 'start': start, 'end': end}, follow=True)

        # Teacher download ranking
        self.assertEqual(
            response.get('Content-Disposition'),
            "attachment; filename=ranking.xlsx",
        )
        self.assertEqual(
            response.get('Content-Type'),
            "application/xlsx"
        )

        file = tempfile.NamedTemporaryFile(mode='w+b', buffering=-1, suffix='.xlsx')
        cont = response.content
        file.write(cont)
        work = openpyxl.load_workbook(file)
        book = work.active
        self.assertIn("Colección: " + collection.name_md, book.cell(row=1, column=1).value)
        self.assertIn("1A", book.cell(row=3, column=1).value)
        self.assertIn("1", book.cell(row=5, column=1).value)
        self.assertIn(user.username, book.cell(row=5, column=2).value)
        self.assertIn("0/1 (1)", book.cell(row=5, column=3).value)
        self.assertIn("0", book.cell(row=5, column=4).value)
        self.assertIn("0", book.cell(row=5, column=5).value)
        file.close()

        # Date or group invalid
        response = client.get(url, {
            'group': group_a.id, 'start': start, 'end': ''}, follow=True)
        self.assertIn("field is required", response.content.decode('utf-8'))
        response = client.get(url, {
            'group': group_a.id, 'start': 'eee', 'end': end}, follow=True)
        self.assertIn("Enter a valid date", response.content.decode('utf-8'))
        response = client.get(url, {
            'group': group_a.id, 'end': end}, follow=True)
        self.assertIn("field is required",
                      response.content.decode('utf-8'))
        response = client.get(url,
                              {'group': '1A', 'start': start, 'end': end}, follow=True)
        self.assertIn('Enter a whole number', response.content.decode('utf-8'))

        # User can't download ranking
        client.logout()
        client.login(username=user.username, password='2222')
        response = client.get(url, {'group': group_a.id, 'start': start, 'end': end}, follow=True)
        self.assertIn('Forbidden', response.content.decode('utf-8'))
