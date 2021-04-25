# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Custom tags for generating random values to be used in templates.
"""

import random
import string

from django import template

register = template.Library()

# Symbols that can appear in a random ID
__ALPHABET = string.ascii_lowercase + string.ascii_uppercase + string.digits


@register.simple_tag
def random_id(size):
    """ Generates a random ID of 'size' letters and digits """
    size = max(1, size)  # non-positive sizes are considered as 1
    gen_id = ""
    for _ in range(size):
        gen_id += random.choice(__ALPHABET)
    return gen_id
