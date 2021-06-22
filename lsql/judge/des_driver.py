# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2021

Class to connect to DES (Datalog Educational System, http://des.sourceforge.net/) in order to detect
more errors and warnings in SELECT queries and DML problems

Need the environment variable DES_BIN pointing to DES binary
"""
import os
import subprocess
import tempfile
from logzero import logger

from .oracle_driver import clean_sql
from .exceptions import DESException
from .types import DesMessageType


def str_to_des_message_type(code_str) -> DesMessageType:
    """ Translates a string with an integer to a DesMessageType """
    return DesMessageType(int(code_str))


def get_block(output, pos, sep):
    """ Returns the current block of output from 'pos' to the next separator in the list of 'sep'.
        Also returns the position where there the first separator of the list 'sep' is
    """
    sep_pos = list()
    for separator in sep:
        sep_pos.append(output.find(separator, pos))
    first_separator = min([s for s in sep_pos if s >= 0])  # Position of the first separator found (discarding -1)
    current_block = output[pos:first_separator]
    return current_block, first_separator


def parse_tapi_error_messages(output, pos):
    """ Returns the list of DES error messages (Type, Message) until the next '$eot', starting from pos """
    msgs = list()
    current_msg, pos = get_block(output, pos, ['\n'])
    pos += 1
    while current_msg != "$eot":
        error_number, pos = get_block(output, pos, ['\n'])
        pos += 1
        error_type = str_to_des_message_type(error_number)
        content, pos = get_block(output, pos, ['\n$error\n', '\n$eot\n', '\n$\n'])
        if output[pos:pos+3] == '\n$\n':
            pos += 3
            snippet, pos = get_block(output, pos, ['$error', '$eot'])
        else:
            snippet = None
            pos += 1
        msgs.append((error_type, content, snippet))
        current_msg, pos = get_block(output, pos, ['\n'])
        pos += 1
    return msgs


def parse_tapi_cmd(output: str, pos: int) -> tuple:
    """ Parses the output of a DES TAPI command starting from position 'pos'.
        Returns a tuple containing the position *after* the command output and also the list of messages
        related to the TAPI command (which can be empty if the execution was successful).
    """
    end_line = output.find('\n', pos)
    cmd_result = output[pos:end_line].strip()
    if cmd_result == '$success':
        # For DDL statements: CREATE TABLE, DROP TABLE
        return end_line + 1, []
    if cmd_result == '$eot':
        # For /parse and /mparse and SQL queries that are correct
        return end_line + 1, []
    if cmd_result.isdigit():
        # For INSERT, DELETE, UPDATE statements that affects some rows
        return end_line + 1, []
    if cmd_result == '$error':
        # Output containing one or several messages (error, warning or info)
        end_output = output.find('$eot', pos)
        end_eot = output.find('\n', end_output) + 1
        msgs = parse_tapi_error_messages(output, pos)
        return end_eot, msgs

    raise DESException(f'Unable to parse DES output: <{cmd_result}>')


def parse_tapi_commands(output: str, num_commands: int, pos: int) -> list:
    """ Parses the output of several DES TAPI commands whose output start from position 'pos'.
        Returns a list of lists, with the messages for each TAPI command.
    """
    msg_list = list()
    for _ in range(num_commands):
        pos, msgs = parse_tapi_cmd(output, pos)
        msg_list.append(msgs)
    return msg_list


class DesExecutor:
    """ Class to connect to DES using the TAPI interface """
    __FILE_PREFIX = "des_checker_"
    __DES = None  # Singleton object for DesExecutor

    @classmethod
    def get(cls):
        """Singleton DB"""
        if cls.__DES is None:
            cls.__DES = DesExecutor()
        return cls.__DES

    @staticmethod
    def get_sql_messages_query(create, insert, query):
        """ Invokes DES to obtain all the messages related to the query (error, warning and info).
            Returns a list of tuples (msg_type, text, query_fragment), or None if there is some error when
            executing DES (or timeouts)
        """
        # _, path = tempfile.mkstemp(prefix=self.__FILE_PREFIX, text=True)
        path = '/tmp/ojete'  # TODO: quitar cuando esté todo comprobado
        with open(path, 'w') as input_stream:
            input_stream.write('/type_casting on\n')
            input_stream.write('/sql\n')
            create_statements = clean_sql(create)
            insert_statements = clean_sql(insert)
            for stmt in create_statements + insert_statements:
                input_stream.write("/tapi {}\n".format(stmt.strip().replace('\n', '')))
            input_stream.write("/tapi /mparse\n{}\n$eot\n".format(query))
            input_stream.write("/exit\n")

        des_path = os.environ['DES_BIN']
        try:
            output = subprocess.check_output(f"timeout 10s {des_path} < {path}", shell=True).decode('utf8')
        except subprocess.CalledProcessError as error:
            logger.debug('Error or timeout when invoking DES. Status code: %s. Output: <<%s>>', error.returncode,
                         error.output)
            return None
        # os.remove(path)  # TODO: descomentar
        clean_output = output[output.find('DES-SQL> ') + len('DES-SQL> '):]  # Removes banner from output
        num_commands = len(create_statements) + len(insert_statements) + 1
        msgs = parse_tapi_commands(clean_output, num_commands, pos=0)
        assert len(msgs) == num_commands
        return zip(create_statements + insert_statements + [query], msgs)
