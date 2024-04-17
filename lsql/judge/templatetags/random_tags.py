# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Custom tags for generating random values to be used in templates.
"""

import secrets

from django import template

register = template.Library()


@register.simple_tag
def random_id(size):
    """ Generates a random ID of 'size' bytes in hexadecimal form """
    size = max(1, size)  # non-positive sizes are considered as 1
    return secrets.token_hex(nbytes=size)
