# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Unit tests to check custom tags for templates
"""

import re

from django.test import TestCase
from django.template import Context, Template


class TagsTest(TestCase):
    """Tests for the custom tags"""

    def test_ramdom_id(self):
        """ Generates two random IDs and prints each one twice in the template"""
        template = Template("""
        {% load random_tags %}
              
        {% random_id 15 as id1 %}
        {{ id1 }}
        {{ id1 }}
        {{ id1 }}
        {% random_id 15 as id2 %}
        {{ id2 }}
        {{ id2 }}        
        """)
        context = Context()
        text = template.render(context)

        regexp = r"[a-zA-Z0-9]{15}"
        matches = re.findall(regexp, text)
        self.assertEqual(len(matches), 5)
        self.assertEqual(matches[0], matches[1])
        self.assertEqual(matches[1], matches[2])
        self.assertEqual(matches[3], matches[4])
        self.assertNotEqual(matches[0], matches[4])  # This could be equal with very small probability 1/65^15
