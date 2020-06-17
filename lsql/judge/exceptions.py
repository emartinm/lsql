# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Custom exceptions when accesing the PostgreSQL database in LSQL
"""


class IncorrectNumberOfSentencesException(Exception):
    pass


class ZipFileParsingException(Exception):
    pass


class ProblemInsertException(Exception):
    pass


class DAOException(Exception):
    def __init__(self, error_code, message):
        super().__init__(message)
        self.message=message
        # value from types.DAOStatusCode
        self.error_code = error_code

    def __repr__(self):
        return f'DAOException({self.error_code}, {self.message})'


class ExecutorException(Exception):
    def __init__(self, error_code, message='', statement=''):
        super().__init__(message)
        self.message=message
        # value from types.SelectStatusCode
        self.error_code = error_code
        self.statement = statement

    def __repr__(self):
        return f'ExecutorException({self.error_code}, {self.message}, {self.statement})'
