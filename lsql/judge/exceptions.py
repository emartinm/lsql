# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Custom exceptions when accessing the PostgreSQL database in LSQL
"""


class IncorrectNumberOfSentencesException(Exception):
    """Problem solution with an incorrect number of sentences"""


class ZipFileParsingException(Exception):
    """Error while parsing a ZIP file containing a problem (or a set of problems)"""


class ExecutorException(Exception):
    """Exception when calling the DB executor"""
    def __init__(self, error_code, message='', statement='', position=(0, 0)):
        super().__init__(message)
        self.message = message
        # value from types.SelectStatusCode
        self.error_code = error_code
        self.statement = statement
        self.position = position


class DESException(Exception):
    """ Error while invoking or parsing DES output """
