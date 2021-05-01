 # -*- coding: utf-8 -*-
"""
Copyright Iván Ruiz <ivarui01@ucm.es> 2021

Custom tags for generating language code corresponding css flag class.
"""

from django import template

register = template.Library()


@register.simple_tag
def language_to_flag(code):
    """Generates css flag class for the language code"""
    if code.lower() == 'en':
        return 'flag-icon flag-icon-us'
    return 'flag-icon flag-icon-' + code.lower()

@register.simple_tag
def collection_flags(languages):
    """Generates the necessary css flag classes for the language codes in a list"""
    flags = []
    if languages != ['es']:
        for lang in languages:
            flags.append(language_to_flag(lang))
    return flags
    