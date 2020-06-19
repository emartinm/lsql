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
