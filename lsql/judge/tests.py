# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the LSQL
"""

from django.test import TestCase

from .feedback import pretty_type


class FeedbackTest(TestCase):
    """Test for module feedback"""

    @staticmethod
    def test_class_names():
        """Test for function pretty_type"""
        assert pretty_type("<class 'cx_Oracle.INTEGER'>") == 'INTEGER'
