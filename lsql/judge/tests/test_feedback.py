# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Unit tests for the feedback module
"""

from django.test import TestCase

from judge.feedback import pretty_type, header_to_str, compare_select_results, compare_db_results, \
    compare_function_results, compare_discriminant_db
from judge.types import VeredictCode


class FeedbackTest(TestCase):
    """Tests for module feedback"""

    def test_class_names(self):
        """Test for function pretty_type"""
        self.assertEqual(pretty_type("<class 'cx_Oracle.INTEGER'>"), 'INTEGER')
        self.assertEqual(pretty_type("otro tipo"), 'otro tipo')

    def test_header_to_str(self):
        """Test for header_to_str"""
        header = [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]]
        expected = "(ID: NUMBER, NOMBRE: STRING)"
        self.assertEqual(header_to_str(header), expected)

    def test_compare_select(self):
        """Test for compare_select_results"""
        expected = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                    'rows': [[1, 'a'], [2, 'b']]}
        obtained1 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[2, 'b'], [1, 'a']]}
        obtained2 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a']]}
        obtained3 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a'], [2, 'b'], [3, 'a']]}
        obtained4 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a'], [2, 'b'], [1, 'a']]}
        obtained5 = {'header': [['IDi', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a'], [2, 'b']]}
        obtained6 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.NUMBER'>"]],
                     'rows': [[1, 'a'], [2, 'b']]}
        obtained7 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"]],
                     'rows': [[1], [2]]}
        obtained8 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"],
                                ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a', 'a'], [2, 'b', 'b']]}

        # Expected equal to obtained
        self.assertEqual(compare_select_results(expected, expected, True)[0], VeredictCode.AC)
        self.assertEqual(compare_select_results(expected, expected, False)[0], VeredictCode.AC)
        # Obtained rows are correct but in other order
        self.assertEqual(compare_select_results(expected, obtained1, False)[0], VeredictCode.AC)
        self.assertEqual(compare_select_results(expected, obtained1, True)[0], VeredictCode.WA)
        # Missing row in obtained
        self.assertEqual(compare_select_results(expected, obtained2, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained2, True)[0], VeredictCode.WA)
        # Extra row in obtained
        self.assertEqual(compare_select_results(expected, obtained3, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained3, True)[0], VeredictCode.WA)
        # Extra row in obtained, and the extra row is a duplicate of other row
        self.assertEqual(compare_select_results(expected, obtained4, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained4, True)[0], VeredictCode.WA)
        # Obtained headers have a row with a different name
        self.assertEqual(compare_select_results(expected, obtained5, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained5, True)[0], VeredictCode.WA)
        # Obtained headers have a row with a different type
        self.assertEqual(compare_select_results(expected, obtained6, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained6, True)[0], VeredictCode.WA)
        # Obtained headers have less columns
        self.assertEqual(compare_select_results(expected, obtained7, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained7, True)[0], VeredictCode.WA)
        # Obtained headers have more columns
        self.assertEqual(compare_select_results(expected, obtained8, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained8, True)[0], VeredictCode.WA)

    def test_feedback_headers(self):
        """Test for feedback_headers"""
        expected = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                    'rows': [[1, 'a'], [2, 'b']]}
        obtained1 = {'header': [['NOMBRE', "<class 'cx_Oracle.STRING'>"], ['ID', "<class 'cx_Oracle.NUMBER'>"]],
                     'rows': [['b', 2], ['a', 1]]}
        obtained2 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"],
                                ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a', 'a'], [2, 'b', 'b']]}

        obtained3 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"]],
                     'rows': [[1], [2]]}

        obtained4 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.NUMBER'>"]],
                     'rows': [[1, 'a'], [2, 'b']]}
        obtained5 = {'header': [['id', "<class 'cx_Oracle.NUMBER'>"], ['nombre', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a'], [2, 'b']]}
        obtained6 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['nombre', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a'], [2, 'b']]}
        obtained7 = {'header': [['Id', "<class 'cx_Oracle.NUMBER'>"], ['NoMbre', "<class 'cx_Oracle.STRING'>"]],
                     'rows': [[1, 'a'], [2, 'b']]}
        # Comprobacion correcta
        self.assertEqual(compare_select_results(expected, expected, True)[0], VeredictCode.AC)
        self.assertEqual(compare_select_results(expected, expected, False)[0], VeredictCode.AC)

        # Comprobacion correcta con minusculas y mayusculas
        self.assertEqual(compare_select_results(expected, obtained5, False)[0], VeredictCode.AC)
        self.assertEqual(compare_select_results(expected, obtained6, False)[0], VeredictCode.AC)
        self.assertEqual(compare_select_results(expected, obtained7, False)[0], VeredictCode.AC)

        # Comprobacion de que salen WA
        self.assertEqual(compare_select_results(expected, obtained2, True)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained2, False)[0], VeredictCode.WA)

        # Obtenido con mas filas que el esperado, compruebo sus mensajes
        self.assertIn("Esperado: 2 columnas", compare_select_results(expected, obtained2, True)[1])
        self.assertIn("Generado por tu código SQL: 3 columnas", compare_select_results(expected, obtained2, True)[1])
        self.assertIn("Número de columnas obtenidas:", compare_select_results(expected, obtained2, True)[1])

        self.assertIn("Esperado: 2 columnas", compare_select_results(expected, obtained2, False)[1])
        self.assertIn("Generado por tu código SQL: 3 columnas", compare_select_results(expected, obtained2, False)[1])
        self.assertIn("Número de columnas obtenidas:", compare_select_results(expected, obtained2, False)[1])

        # Comprobacion de que salen WA
        self.assertEqual(compare_select_results(expected, obtained3, True)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained3, False)[0], VeredictCode.WA)

        # Obtenido con menos filas que el esperado, compruebo sus mensajes
        self.assertIn("Esperado: 2 columnas", compare_select_results(expected, obtained3, True)[1])
        self.assertIn("Generado por tu código SQL: 1 columnas", compare_select_results(expected, obtained3, True)[1])
        self.assertIn("Número de columnas obtenidas:", compare_select_results(expected, obtained3, True)[1])

        self.assertIn("Esperado: 2 columnas", compare_select_results(expected, obtained3, False)[1])
        self.assertIn("Generado por tu código SQL: 1 columnas", compare_select_results(expected, obtained3, False)[1])
        self.assertIn("Número de columnas obtenidas:", compare_select_results(expected, obtained3, False)[1])

        # Comprobacion de que salen WA
        self.assertEqual(compare_select_results(expected, obtained1, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained1, True)[0], VeredictCode.WA)

        # Comprobacion de que las columnas estan cambiadas Esperado: ID NOMBRE y obtengo NOMBRE ID
        self.assertIn("nombre de la 1ª columna", compare_select_results(expected, obtained1, False)[1])
        self.assertIn("Nombre esperado: ID", compare_select_results(expected, obtained1, False)[1])
        self.assertIn("Nombre generado por tu código SQL: NOMBRE",
                      compare_select_results(expected, obtained1, False)[1])

        # Comprobacion de que salen WA
        self.assertEqual(compare_select_results(expected, obtained4, False)[0], VeredictCode.WA)
        self.assertEqual(compare_select_results(expected, obtained4, True)[0], VeredictCode.WA)

        # Comprobacion de que los tipos no son los adecuados
        self.assertIn("Tipo generado por tu código SQL: ", compare_select_results(expected, obtained4, True)[1])
        self.assertIn("tipo de la columna NOMBRE", compare_select_results(expected, obtained4, False)[1])

    def test_compare_db(self):
        """Tests for compare_db_results"""
        table1 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                  'rows': [[1, 'a'], [2, 'b']]}
        table2 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                  'rows': [[1, 'zzzz'], [2, 'b']]}
        table3 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                  'rows': [[2, 'b'], [1, 'a']]}
        expected = {'table1': table1, 'table2': table1}
        obtained1 = {'table1': table1}
        obtained2 = {'table1': table1, 'table2': table1, 'table3': table1}
        obtained3 = {'table1': table1, 'table2': table2}
        obtained4 = {'table1': table1, 'table2': table3}

        # Identical DB
        self.assertEqual(compare_db_results(expected, expected)[0], VeredictCode.AC)
        # Missing table
        self.assertEqual(compare_db_results(expected, obtained1)[0], VeredictCode.WA)
        # Extra table
        self.assertEqual(compare_db_results(expected, obtained2)[0], VeredictCode.WA)
        # Number and types of tables correct, but one table has different tuples
        self.assertEqual(compare_db_results(expected, obtained3)[0], VeredictCode.WA)
        # Number and types of tables correct, but one differs in order
        self.assertEqual(compare_db_results(expected, obtained4)[0], VeredictCode.AC)

    def test_compare_function(self):
        """Tests for compare_function_results"""
        expected = {'fun(1)': 3, 'fun(2)': 56}
        obtained1 = {'fun(1)': 3, 'fun(2)': 5}
        obtained2 = {'fun(1)': 33, 'fun(2)': 56}

        # Identical
        self.assertEqual(compare_function_results(expected, expected)[0], VeredictCode.AC)
        # Wrong result in first call
        self.assertEqual(compare_function_results(expected, obtained2)[0], VeredictCode.WA)
        # Wrong result in second call
        self.assertEqual(compare_function_results(expected, obtained1)[0], VeredictCode.WA)

    def test_discriminant_feedback(self):
        """Test for compare discriminant type problems feedback"""
        header_e = {'header': [['id', "<class 'cx_Oracle.NUMBER'>"], ['nombre', "<class 'cx_Oracle.STRING'>"]],
                    'rows': [[1, 'a'], [2, 'b']]}
        header_o = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"]], 'rows': [[1], [2]]}
        ac_e = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                  'rows': [[1, 'a'], [2, 'b']]}
        ac_o = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['NOMBRE', "<class 'cx_Oracle.STRING'>"]],
                  'rows': [[1, 'a']]}
        order_1 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['PK', "<class 'cx_Oracle.NUMBER'>"]],
                  'rows': [[1, 1], [2, 2]]}
        order_2 = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['PK', "<class 'cx_Oracle.NUMBER'>"]],
                  'rows': [[2, 2], [1, 1]]}
        order_2_bis = {'header': [['ID', "<class 'cx_Oracle.NUMBER'>"], ['PK', "<class 'cx_Oracle.NUMBER'>"]],
                   'rows': [[2, 2], [1, 1]]}
        # Incorrect headers
        self.assertEqual(compare_discriminant_db(header_e, header_o, False)[0], VeredictCode.WA)
        # Correct answer
        self.assertEqual(compare_discriminant_db(ac_e, ac_o, False)[0], VeredictCode.AC)
        # Correct answer with order
        self.assertEqual(compare_discriminant_db(order_1, order_2, True)[0], VeredictCode.AC)
        # Incorrect answer with order
        self.assertIn('La inserción que has propuesto no permite detectar el comportamiento erróneo de la sentencia.',
                      compare_discriminant_db(order_2, order_2_bis, True)[1])
        # Incorrect answer without order
        self.assertIn('La inserción que has propuesto no permite detectar el comportamiento erróneo de la sentencia.',
                      compare_discriminant_db(ac_o, ac_e, False)[1])
