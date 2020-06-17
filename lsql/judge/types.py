# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Types used in LSQL
"""

from enum import IntEnum, unique


@unique
class ProblemType(IntEnum):
    SELECT = 0,
    DML = 1,
    FUNCTION = 2,
    PROC = 3,
    TRIGGER = 4


@unique
class VeredictCode(IntEnum):
    AC = 1
    TLE = 2
    RE = 3
    WA = 4
    INTERNAL_ERROR = 5,
    VALIDATION_ERROR = 6

    def short_name(self):
        mapping = {
            VeredictCode.VALIDATION_ERROR: 'Error de validación',
            VeredictCode.AC: 'Aceptado',
            VeredictCode.TLE: 'Tiempo límite excedido',
            VeredictCode.RE: 'Error en ejecución',
            VeredictCode.WA: 'Resultados incorrectos',
            VeredictCode.INTERNAL_ERROR: 'Error interno'
        }
        return mapping[self.value]

    def html_short_name(self):
        if self.value == VeredictCode.AC:
            return f'<span class="text-success">{self.short_name()}</span>'
        else:
            return f'<span class ="text-danger">{self.short_name()}</span>'


@unique
class UserType(IntEnum):
    TEACHER = 1,
    STUDENT = 2


@unique
class OracleStatusCode(IntEnum):
    OK = 0,
    GET_ADMIN_CONNECTION = 1,
    CREATE_USER = 2,
    EXECUTE_CREATE = 3,
    EXECUTE_INSERT = 4,
    EXECUTE_USER_CODE = 5,
    NUMBER_STATEMENTS = 6,
    DROP_USER = 7,
    RELEASE_ADMIN_CONNECTION = 8,
    CLOSE_USER_CONNECTION = 9,
    GET_USER_CONNECTION = 10,
    OTHER = 11,
    GET_ALL_TABLES = 12,
    COMPILATION_ERROR = 13,
    TLE_USER_CODE = 14


@unique
class DAOStatusCode(IntEnum):
    OK = 0,
    POOL_ERROR = 1,
    NOT_FOUND = 2,
    PROBLEM_DATA_NOT_FOUND = 3,
    OTHER_ERROR = 4
