# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the LSQL
"""

from django.test import TestCase

from .feedback import pretty_type, header_to_str


class FeedbackTest(TestCase):
    """Test for module feedback"""

    @staticmethod
    def test_class_names():
        """Test for function pretty_type"""
        assert pretty_type("<class 'cx_Oracle.INTEGER'>") == 'INTEGER'

    @staticmethod
    def test_header_to_str():
        header = [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]]
        expected = "(ID: NUMBER, NOMBRE: STRING)"
        assert header_to_str(header) == expected
