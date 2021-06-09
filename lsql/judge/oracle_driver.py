# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Class to connect to Oracle and execute the different types of problems
"""

# Needs to use cx_Oracle
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/kike/xDownload/instantclient_19_6

import time
import string
import random
import os
import re
import json
import cx_Oracle
from logzero import logger
import sqlparse

from django.core.serializers.json import DjangoJSONEncoder

from .exceptions import ExecutorException
from .types import OracleStatusCode


def replace_rest_stmt_blanks(statements):
    """ Given a list[str] of SQL statements extends every statement with as many spaces and newlines as the previous
        and next statements. This way, executing each statement separately will produce the error in the same offset
        position as the complete SQL block, so they could be shown correctly in the editor. For example:

            'SELECT *\nFROM CLUB;\nSELECT *\nFROM CLUB;'          --> (Origina block code)
           ['SELECT *\nFROM CLUB;', '\nSELECT *\nFROM CLUB;']     --> (Split statements)
           ['SELECT *\nFROM CLUB;\n        \n          ',         --> (Split statements with equal length and \n)
            '        \n          \nSELECT *\nFROM CLUB;'
    """
    num_stmt = len(statements)
    result = []
    for i in range(num_stmt):
        pre = re.sub(r'\S', ' ', "".join(statements[:i]))
        post = re.sub(r'\S', ' ', "".join(statements[i+1:]))
        result.append(pre + statements[i] + post)
    return result


def clean_sql(code: str, min_stmt: int = None, max_stmt: int = None):
    """
    Parses SQL code into statements (removing comments and ';').
    :param code: str containing SQL code
    :param min_stmt: minimum number of statements
    :param max_stmt: maximum number of statements
    :return: [str] if code is a sequence between min_stmt and max_stmt correct SQL statements, otherwise None
    """
    if code is None:
        code = ""
    # Replaces every line comment by a sequence of spaces of the same length
    code_no_comments = re.sub(r'--.*$', lambda match_obj: ' '*len(match_obj.group(0)), code, flags=re.MULTILINE)
    # Splits statements and replaces \r by spaces (only \n for newline)
    statements = [str(s).replace('\r', ' ') for s in sqlparse.parse(code_no_comments)]  # Uses only \n for newline
    # Replaces the last ';' of each statement with spaces
    statements = [re.sub(r';\s*$', lambda match_obj: ' '*len(match_obj.group(0)), s, flags=re.MULTILINE)
                  for s in statements]
    statements = replace_rest_stmt_blanks(statements)
    num_sql = len(statements)
    if (min_stmt and num_sql < min_stmt) or (max_stmt and num_sql > max_stmt):
        statements = None
    return statements


def random_str(alphabet, size=8):
    """
    Creates a random string of 'n' letters from 'alphabet'
    :param alphabet: Candidate letters
    :param size: Length of the generated random string
    :return: Random string of 'n' letters from 'alphabet'
    """
    ret = ''
    for _ in range(size):
        ret += random.choice(alphabet)
    return ret


def line_col_from_offset(code: str, offset: int):
    """
    Returns the line and columns of an offset in a code
    :param offset:
    :param code:
    :return: pair (int, int) of (line, col)
    """
    line = 0
    last_line_init = 0
    for i in range(offset):
        if code[i] == '\n':
            last_line_init = i+1
            line += 1
    col = offset - last_line_init
    return line, col


def uniform_dict(dictionary):
    """
    Uses DjangoJSONEncoder to represent as strings those values that are not directly serialized (like datetime)
    :param dictionary: Python dictionary
    :return: Python dictionary with all the fields uniformly represented
    """
    string_rep = json.dumps(dictionary, cls=DjangoJSONEncoder)
    return json.loads(string_rep)


def table_from_cursor(cursor):
    """
    Takes a cursor that has executed a SELECT statement and returns all the results
    in a dictionary. It checks if the number of columns in the cursor exceeds
    ORACLE_MAX_COLS or the number of rows exceeds ORACLE_MAX_ROWS. In those cases
    raises an ExecutorException with status code OracleStatusCode.TLE_USER_CODE
    :param cursor: DB cursor
    :return: a dictionary {'header':[[NAME:str, TYPE:str]], 'rows': [list]}
    """
    max_rows = int(os.environ['ORACLE_MAX_ROWS'])
    max_cols = int(os.environ['ORACLE_MAX_COLS'])
    table = dict()

    if cursor.description is None:
        # It's the result of an SQL statement that do not return results (CREATE VIEW, for example)
        table['header'] = list()
        table['rows'] = list()
        return table  # return empty table (no columns, no rows)

    if len(cursor.description) > max_cols:
        logger.debug('TLE caused by too many columns in cursor')
        raise ExecutorException(OracleStatusCode.TLE_USER_CODE)
    table['header'] = [[e[0], str(e[1])] for e in cursor.description]

    batch = cursor.fetchmany(numRows=max_rows)  # Takes MAX rows
    if cursor.fetchone():  # There are more rows
        logger.debug('TLE caused by too many rows in cursor')
        raise ExecutorException(OracleStatusCode.TLE_USER_CODE)
    table['rows'] = [list(e) for e in batch]

    return uniform_dict(table)  # Represents datetime as uniform strings


def get_all_tables(conn):
    """
    Returns a dictionary representing all the tables in the DB. It checks if the
    number of tables owned by the user exceeds ORACLE_MAX_TABLES, and raises an
    ExecutorException with status code OracleStatusCode.TLE_USER_CODE
    :param conn: DB connection
    :return: dictionary {table_name: TABLE}, where TABLE is the dictionary
             generated by table_from_cursor
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT table_name FROM USER_TABLES")
        tables = cursor.fetchmany(int(os.environ['ORACLE_MAX_TABLES']))
        if cursor.fetchone():
            logger.debug('Too many tables in user DB')
            raise ExecutorException(OracleStatusCode.TLE_USER_CODE)
        tb_names = [e[0] for e in tables]
        db_dict = dict()
        for table_name in tb_names:
            # https://docs.oracle.com/database/121/SQLRF/sql_elements008.htm#SQLRF51129
            # Quoted names should be embedded with "..." in order to work. We try
            # both versions for table names, ignoring possible exceptions.
            try:
                cursor.execute("SELECT * FROM {}".format(table_name))  # Direct name
            except cx_Oracle.DatabaseError:
                cursor.execute('SELECT * FROM "{}"'.format(table_name))  # Quoted name
            table = table_from_cursor(cursor)
            db_dict[table_name] = table

        return db_dict


def execute_select_statement(conn, statement):
    """
    Given a connection to an Oracle database, executes a string containing exactly ONE statement
    :param conn: Oracle connection
    :param statement: String containing one SQL Select statement
    :return: List with the results of the SELECT statement. It raises an IncorrectNumberOfSentences
             exception if 'statement' contains more than one SQL statement, and a
             cx_Oracle.DatabaseError if the execution of the statements is not correct
    """
    init = time.time()
    statements = clean_sql(statement)
    if len(statements) != 1:
        logger.debug('User %s - <<%s>> contains more than one SQL statement',
                     conn.username, statement)
        raise ExecutorException(OracleStatusCode.NUMBER_STATEMENTS)

    with conn.cursor() as cursor:
        cursor.execute(statements[0])
        logger.debug('User %s - SQL select statement <<%s>> executed in %s seconds',
                     conn.username, statement, time.time() - init)
        table = table_from_cursor(cursor)
    return table


def execute_dml_statements(conn, dml, min_stmt=0, max_stmt=float("inf")):
    """
    Given a connection to an Oracle database, executes a string containing DML statements
    :param min_stmt:
    :param max_stmt:
    :param conn: Oracle connection
    :param dml: String containing DML statements
    :return: None
    """
    init = time.time()
    statements = clean_sql(dml, min_stmt, max_stmt)
    with conn.cursor() as cursor:
        for stmt in statements:
            cursor.execute(stmt)
            logger.debug('User %s - SQL DML statement <<%s>> executed in %s seconds',
                         conn.username, stmt, time.time() - init)
        conn.commit()


def execute_sql_script(conn, script):
    """
    Given an Oracle connection, executes a script formed by one or more statements
    :param conn: Oracle connection
    :param script: String containing one or more SQL statements (DDL, DML, etc)
    :return: None. It raises a cx_Oracle.DatabaseError if the execution of any of the
             statements is not correct.
    """
    init = time.time()
    statements = clean_sql(script)
    if len(statements) > 0:
        with conn.cursor() as cursor:
            for statement in statements:
                logger.debug('Executing SQL statement <<%s>>', statement)
                cursor.execute(statement)
            conn.commit()
            logger.debug('User %s - SQL script <<%s>> executed in %s seconds',
                         conn.username, statements, time.time() - init)


def get_compilation_errors(conn):
    """
    Extracts compilation errors from table SYS.USER_ERRORS and returns
    :param conn: Open Oracle connection
    :return: dict representing the table
    """
    with conn.cursor() as cursor:
        cursor.execute('''SELECT NAME "Nombre de procedimiento", LINE "Línea", POSITION "Posición",
                                 TEXT "Error detectado", ATTRIBUTE "Criticidad" 
                          FROM SYS.USER_ERRORS''')
        return table_from_cursor(cursor)


def offset_from_oracle_exception(excp: cx_Oracle.DatabaseError) -> int:
    """Extracts the offset from a DataBaseError"""
    # pylint: disable = no-member
    # Locally disabled memeber checks because pylint thinks oracle_error is str
    oracle_error, = excp.args
    return oracle_error.offset


# Dropping users will automatically remove all their objects
# I keep this function just in case is useful in the future
# def empty_schema(conn):
#     """
#     Completely empties the current schema in the connection, i.e., drops all user objects.
#     Captures any exception caused by any DROP statement or the SELECT used to find user objects
#     :param conn: open connection to an Oracle DB
#     :return: bool
#     """
#     init = time.time()
#     correct = True
#     try:
#         sql = """
#             select 'DROP '||object_type||' '|| object_name|| DECODE(OBJECT_TYPE,'TABLE',' CASCADE CONSTRAINTS','')
#             from user_objects"""
#         with conn.cursor() as cursor:
#             cursor.execute(sql)
#             drop_statements = [p[0] for p in cursor]
#             for drop in drop_statements:
#                 cursor.execute(drop)
#     except cx_Oracle.DatabaseError:
#         correct = False
#
#     if correct:
#         logger.debug('User %s - Schema deleted in %s seconds',
#                      conn.username, time.time() - init)
#     else:
#         logger.error('User %s - Unable to delete schema', conn.username)
#     return correct


def build_dsn_tns():
    """Build a Data Source Name from values in the environment"""
    dsn_tns = cx_Oracle.makedsn(
        os.environ['ORACLE_SERVER'],
        int(os.environ['ORACLE_PORT']),
        os.environ['ORACLE_SID'])
    return dsn_tns


class OracleExecutor:
    """Class to connect to Oracle DB and execute problems"""

    __USER_PREFIX = 'lsql_'
    __ALPHABET = string.ascii_lowercase + string.digits
    __CREATE_USER_SCRIPT = ('CREATE USER {} '
                            'IDENTIFIED BY "{}" '
                            'DEFAULT TABLESPACE {} '
                            'TEMPORARY TABLESPACE TEMP QUOTA UNLIMITED ON {}')
    __GRANT_USER_SCRIPT = ('GRANT create table, delete any table, select any dictionary, connect, create session , '
                           'create synonym , create public synonym, create sequence, create view , '
                           'create trigger, alter any trigger, drop any trigger, '
                           'create procedure, alter any procedure, drop any procedure, execute any procedure '
                           'TO {}')
    __DROP_USER_SCRIPT = 'DROP USER {} CASCADE'
    __USER_CONNECTIONS = """SELECT s.sid, s.serial#, s.username
                                FROM   gv$session s
                                       JOIN gv$process p ON p.addr = s.paddr AND p.inst_id = s.inst_id
                                WHERE  s.username = :username"""
    __DANGLING_USERS = """SELECT USERNAME, CREATED
                          FROM all_users
                          WHERE USERNAME LIKE 'LSQ_%' AND (SYSDATE-CREATED)*24*60*60 > :age_seconds
                          ORDER BY CREATED ASC"""
    __NUM_DANGLING_USERS = """SELECT COUNT(USERNAME)
                              FROM all_users
                              WHERE USERNAME LIKE 'LSQ_%' AND (SYSDATE-CREATED)*24*60*60 > :age_seconds"""
    __KILL_SESSION = """ALTER SYSTEM KILL SESSION '{},{}'"""
    __SLEEP_AFTER_TIMEOUT = 100
    # milliseconds to sleep after a timeout when obtaining a
    # a timeout error, so that user connections can be properly
    # closed (otherwise, DROP USER throws an 'ORA-01940: cannot
    # drop a user that is currently connected')

    __DB = None

    @classmethod
    def get(cls):
        """Singleton DB"""
        if cls.__DB is None:
            cls.__DB = OracleExecutor()
        return cls.__DB

    def __init__(self):
        """
        Creates a pool of connections with the admin user, taking the details from
        the configuration file. Throws a cx_Oracle.DatabaseError if it is not
        possible to create the pool
        """
        self.dsn_tns = build_dsn_tns()
        self.connection_pool = cx_Oracle.SessionPool(
            os.environ['ORACLE_USER'],
            os.environ['ORACLE_PASS'],
            self.dsn_tns,
            threaded=True,
            encoding='UTF-8', nencoding='UTF-8',
            min=1,
            max=int(os.environ['ORACLE_MAX_GESTOR_CONNECTIONS']),
            getmode=cx_Oracle.SPOOL_ATTRVAL_TIMEDWAIT,
            waitTimeout=int(os.environ['ORACLE_GESTOR_POOL_TIMEOUT_MS'])
        )
        self.version = None
        logger.debug('Created an OracleExecutor to %s with a pool of %s connections with a timeout of %s ms',
                     self.dsn_tns,
                     int(os.environ['ORACLE_MAX_GESTOR_CONNECTIONS']),
                     int(os.environ['ORACLE_GESTOR_POOL_TIMEOUT_MS'])
                     )

    def get_version(self):
        """Returns the version of the Oracle server"""
        if not self.version:
            gestor = self.connection_pool.acquire()
            self.version = f'Oracle {gestor.version}'
            self.connection_pool.release(gestor)
        return self.version

    def create_user(self, connection):
        """
        Creates a new user in the local Oracle DB with a random name and password. The user
        has acces to the TABLESPACE defined in the configuration file, and its username
        starts with a given prefix defined in the configuration file
        :param connection: Connection with privileges for creating users
        :return: A pair (username, password) of the created user
        """
        user_name = self.__USER_PREFIX + random_str(self.__ALPHABET)
        user_passwd = random_str(self.__ALPHABET)
        create_script = self.__CREATE_USER_SCRIPT.format(
            user_name,
            user_passwd,
            os.environ['ORACLE_TABLESPACE'],
            os.environ['ORACLE_TABLESPACE']
        )
        grant_script = self.__GRANT_USER_SCRIPT.format(user_name)

        with connection.cursor() as cursor:
            cursor.execute(create_script)
            logger.debug('User %s - Created user %s', connection.username, user_name)
            cursor.execute(grant_script)
        logger.debug('User %s - Granted privileges to user %s', connection.username, user_name)
        return user_name, user_passwd

    def remove_dangling_users(self, age_seconds=60):
        """
        Removes all the LSQL_* users created more than 'age_seconds' ago
        :param age_seconds: (int) number of seconds
        :return: None
        """
        gestor = None
        try:
            gestor = self.connection_pool.acquire()
            with gestor.cursor() as cursor:
                cursor.execute(self.__DANGLING_USERS, age_seconds=age_seconds)
                users = cursor.fetchall()
                for user in users:
                    logger.info('Removing dangling user %s created at %s', user[0], user[1])
                    cursor.execute(self.__USER_CONNECTIONS, username=user[0])
                    connections = cursor.fetchall()
                    # Kills all the possible connections of username
                    for connection in connections:  # pragma: no cover
                        cursor.execute(self.__KILL_SESSION.format(connection[0], connection[1]))
                    self.drop_user(user[0], gestor)
        except cx_Oracle.DatabaseError as excp:  # pragma: no cover
            logger.error('Unable to remove dangling users. Reason: %s', excp)
        finally:
            if gestor is not None:
                self.connection_pool.release(gestor)

    def get_number_dangling_users(self, age_seconds=60):
        """
        Returns the number of dangling users, i.e., users created more than 'age_seconds' ago
        :param age_seconds: (int) number of seconds
        :return: (int), -1 if error
        """
        gestor = None
        num = -1
        try:
            gestor = self.connection_pool.acquire()
            with gestor.cursor() as cursor:
                cursor.execute(self.__NUM_DANGLING_USERS, age_seconds=age_seconds)
                row = cursor.fetchone()
                num = row[0]
        except cx_Oracle.DatabaseError as excp:  # pragma: no cover
            logger.error('Unable to get number of dangling users. Reason: %s', excp)
        finally:
            if gestor is not None:
                self.connection_pool.release(gestor)
        return num

    def drop_user(self, user_name, connection):
        """
        Removes a user from the Oracle local DB
        :param user_name: Name of the user to remove
        :param connection: Connection with priviledges to drop users
        :return: None
        """
        with connection.cursor() as cursor:
            cursor.execute(self.__USER_CONNECTIONS, username=user_name)
            active_connections = cursor.fetchall()
            logger.debug('User %s has %s active connections', user_name, len(active_connections))
            drop_script = self.__DROP_USER_SCRIPT.format(user_name)
            cursor.execute(drop_script)
        logger.debug('User %s - Dropped user %s', connection.username, user_name)

    def create_connection(self, user, passwd):
        """
        Creates an Oracle connection to localhost/xe using UTF-8
        :param user: Name of the Oracle user
        :param passwd: Password of the Oracle user
        :return: Oracle connection
        """
        connection = cx_Oracle.connect(user, passwd, self.dsn_tns, encoding='UTF-8', nencoding='UTF-8')
        return connection

    def execute_select_test(self, creation, insertion, select, output_db=False):
        """
        Using a new fresh user, creates a set of tables ('creation) and inserts some data.
        Then, executes a correct SELECT statement and also a SELECT statement to test
        :param output_db:
        :param creation: (str) Statements to create the tables and other structures
        :param insertion: (str) Statements to insert data into tables
        :param select: (str) One SELECT statement to execute
        :return: {"result": result, "db": db}. result is a dictionary representing the statement result, and db is a
                 dictionary representing all the tables. In case of error, throws a ExecutorException
        """
        conn, gestor, result, user, db = None, None, None, None, None
        state = OracleStatusCode.GET_ADMIN_CONNECTION
        try:
            gestor = self.connection_pool.acquire()

            state = OracleStatusCode.CREATE_USER
            user, passwd = self.create_user(gestor)

            state = OracleStatusCode.GET_USER_CONNECTION
            conn = self.create_connection(user, passwd)

            conn.callTimeout = int(os.environ['ORACLE_STMT_TIMEOUT_MS'])
            state = OracleStatusCode.EXECUTE_CREATE
            execute_sql_script(conn, creation)

            state = OracleStatusCode.EXECUTE_INSERT
            execute_sql_script(conn, insertion)

            state = OracleStatusCode.EXECUTE_USER_CODE
            result = execute_select_statement(conn, select)

            state = OracleStatusCode.GET_ALL_TABLES
            if output_db:
                db = get_all_tables(conn)

            state = OracleStatusCode.CLOSE_USER_CONNECTION
            conn.close()
            conn = None

            state = OracleStatusCode.DROP_USER
            self.drop_user(user, gestor)
            user = None

            state = OracleStatusCode.RELEASE_ADMIN_CONNECTION
            self.connection_pool.release(gestor)
            gestor = None
            return {"result": result, "db": db}
        except cx_Oracle.DatabaseError as excp:
            error_msg = str(excp)
            logger.info('Error when testing SELECT statements: %s - %s - %s', state, excp, select)
            if ('ORA-3156' in error_msg or 'ORA-24300' in error_msg) and state == OracleStatusCode.EXECUTE_USER_CODE:
                # Time limit exceeded
                raise ExecutorException(OracleStatusCode.TLE_USER_CODE, error_msg, select) from excp
            pos = line_col_from_offset(select, offset_from_oracle_exception(excp))
            raise ExecutorException(state, error_msg, select, pos) from excp
        finally:
            if conn:
                conn.close()
            if user:
                try:
                    # Sometimes when TLE, the connections can be closed but the user cannot be dropped because
                    # "is currently connected". This looks like a bug or undocumented behavior of cx_Oracle
                    # These users must be removed manually later
                    self.drop_user(user, gestor)
                except cx_Oracle.DatabaseError as drop_except:  # pragma: no cover
                    logger.error('Unable to drop user %s, REMOVE IT MANUALLY (%s)', user, drop_except)
            if gestor:
                self.connection_pool.release(gestor)

    def execute_dml_test(self, creation, insertion, dml, pre_db=True, min_stmt=0, max_stmt=float("inf")):
        """
        Using a new fresh user, creates a set of tables ('creation) and inserts some data.
        Then, executes some DML statements
        :param max_stmt:
        :param min_stmt:
        :param pre_db:
        :param creation: (str) Statements to create the tables and other structures
        :param insertion: (str) Statements to insert data into tables
        :param dml: (str) DML statements to execute (insert, delete, update)
        :return: {'pre': DB, 'post': DB} dictionary containing the state of the DB before and after executing dml
        """
        conn, gestor, user, post, stmt = None, None, None, None, None
        state = OracleStatusCode.GET_ADMIN_CONNECTION
        try:
            gestor = self.connection_pool.acquire()

            state = OracleStatusCode.CREATE_USER
            user, passwd = self.create_user(gestor)

            state = OracleStatusCode.GET_USER_CONNECTION
            conn = self.create_connection(user, passwd)

            conn.callTimeout = int(os.environ['ORACLE_STMT_TIMEOUT_MS'])
            state = OracleStatusCode.EXECUTE_CREATE
            execute_sql_script(conn, creation)

            state = OracleStatusCode.EXECUTE_INSERT
            execute_sql_script(conn, insertion)

            pre = dict()
            if pre_db:
                state = OracleStatusCode.GET_ALL_TABLES
                pre = get_all_tables(conn)

            state = OracleStatusCode.EXECUTE_USER_CODE
            init = time.time()
            statements = clean_sql(dml, min_stmt, max_stmt)
            if not statements:
                logger.debug('User %s - <<%s>> contains unexpected number of statements [%s - %s]',
                             conn.username, statements, min_stmt, max_stmt)
                raise ExecutorException(OracleStatusCode.NUMBER_STATEMENTS)
            with conn.cursor() as cursor:
                for stmt in statements:
                    cursor.execute(stmt)
                conn.commit()

            logger.debug('User %s - SQL DML statements <<%s>> executed in %s seconds',
                         conn.username, statements, time.time() - init)

            state = OracleStatusCode.GET_ALL_TABLES
            post = get_all_tables(conn)

            state = OracleStatusCode.CLOSE_USER_CONNECTION
            conn.close()
            conn = None

            state = OracleStatusCode.DROP_USER
            self.drop_user(user, gestor)
            user = None

            state = OracleStatusCode.RELEASE_ADMIN_CONNECTION
            self.connection_pool.release(gestor)
            gestor = None

            return {'pre': pre, 'post': post}
        except cx_Oracle.DatabaseError as excp:
            error_msg = str(excp)
            logger.info('Error when testing DML statements: %s - %s - %s', state, excp, stmt)
            if ('ORA-3156' in error_msg or 'ORA-24300' in error_msg) and state == OracleStatusCode.EXECUTE_USER_CODE:
                # Time limit exceeded
                raise ExecutorException(OracleStatusCode.TLE_USER_CODE, error_msg, stmt) from excp
            raise ExecutorException(state, error_msg, stmt) from excp
        finally:
            if conn:
                conn.close()
            if user:
                try:
                    # Sometimes when TLE, the connections can be closed but the user cannot be dropped because
                    # "is currently connected". This looks like a bug or undocumented behavior of cx_Oracle
                    # These users must be removed manually later
                    self.drop_user(user, gestor)
                except cx_Oracle.DatabaseError as drop_except:  # pragma: no cover
                    logger.error('Unable to drop user %s, REMOVE IT MANUALLY (%s)', user, drop_except)
            if gestor:
                self.connection_pool.release(gestor)

    def execute_function_test(self, creation, insertion, func_creation, tests):
        """
        Using a new fresh user, creates a set of tables ('creation) and inserts some data.
        Then, executes some DML statements
        :param tests: (str) function calls separated by new lines
        :param func_creation:
        :param creation: (str) Statements to create the tables and other structures
        :param insertion: (str) Statements to insert data into tables

        :return: {'pre': DB, 'results': dict} dictionary containing the initial state of the DB and a dictionary
                 {call: result} with the different calls and its expected result
        """
        conn, gestor, user, stmt = None, None, None, None
        state = OracleStatusCode.GET_ADMIN_CONNECTION
        try:
            gestor = self.connection_pool.acquire()

            state = OracleStatusCode.CREATE_USER
            user, passwd = self.create_user(gestor)

            state = OracleStatusCode.GET_USER_CONNECTION
            conn = self.create_connection(user, passwd)

            conn.callTimeout = int(os.environ['ORACLE_STMT_TIMEOUT_MS'])
            state = OracleStatusCode.EXECUTE_CREATE
            execute_sql_script(conn, creation)

            state = OracleStatusCode.EXECUTE_INSERT
            execute_sql_script(conn, insertion)

            state = OracleStatusCode.GET_ALL_TABLES
            db = get_all_tables(conn)

            state = OracleStatusCode.EXECUTE_USER_CODE
            init = time.time()

            # sqlparse does not consider the whole CREATE FUNCTION as a single statement, so we cannot check
            # the minimum and maximum number of statements in this kind of problems :-(

            with conn.cursor() as cursor:
                stmt = func_creation
                cursor.execute(stmt)

                # Stops if there is some compilation error with the function
                # We must handle it manually because executing a FUNCTION creation with failures does not throw
                # any Oracle exception
                errors = get_compilation_errors(conn)
                if len(errors['rows']) > 0:
                    raise ExecutorException(OracleStatusCode.COMPILATION_ERROR, message=errors, statement=stmt)

                results = dict()
                tests = [s.strip() for s in tests.split('\n') if len(s.strip()) > 0]
                for stmt in tests:
                    func_call = f'SELECT {stmt} FROM DUAL'
                    cursor.execute(func_call)
                    row = cursor.fetchone()
                    results[stmt] = row[0]

            logger.debug('User %s - Function creation and testing executed in %s seconds',
                         conn.username, time.time() - init)

            state = OracleStatusCode.CLOSE_USER_CONNECTION
            conn.close()
            conn = None

            state = OracleStatusCode.DROP_USER
            self.drop_user(user, gestor)
            user = None

            state = OracleStatusCode.RELEASE_ADMIN_CONNECTION
            self.connection_pool.release(gestor)
            gestor = None

            return {'db': db, 'results': results}
        except cx_Oracle.DatabaseError as excp:
            error_msg = str(excp)
            logger.info('Error when testing function statements: %s - %s - %s', state, excp, stmt)
            if ('ORA-3156' in error_msg or 'ORA-24300' in error_msg) and state == OracleStatusCode.EXECUTE_USER_CODE:
                # Time limit exceeded
                raise ExecutorException(OracleStatusCode.TLE_USER_CODE, excp, stmt) from excp
            raise ExecutorException(state, excp, stmt) from excp
        finally:
            if conn:
                conn.close()
            if user:
                try:
                    # Sometimes when TLE, the connections can be closed but the user cannot be dropped because
                    # "is currently connected". This looks like a bug or undocumented behavior of cx_Oracle
                    # These users must be removed manually later
                    self.drop_user(user, gestor)
                except cx_Oracle.DatabaseError as drop_except:  # pragma: no cover
                    logger.error('Unable to drop user %s, REMOVE IT MANUALLY (%s)', user, drop_except)
            if gestor:
                self.connection_pool.release(gestor)

    def execute_proc_test(self, creation, insertion, proc_creation, proc_call, pre_db=True):
        """
        Using a new fresh user, creates a set of tables ('creation) and inserts some data.
        Then, creates a PROCEDURE defined in proc_creation and invokes the call in proc_call
        :param pre_db:
        :param proc_call:
        :param proc_creation:
        :param creation: (str) Statements to create the tables and other structures
        :param insertion: (str) Statements to insert data into tables

        :return: {'pre': DB, 'post': DB} dictionary containing the state of the DB before defining the procedure and
                   and after invoking the procedure
        """
        conn, gestor, user, post, stmt = None, None, None, None, None
        state = OracleStatusCode.GET_ADMIN_CONNECTION
        try:
            gestor = self.connection_pool.acquire()

            state = OracleStatusCode.CREATE_USER
            user, passwd = self.create_user(gestor)

            state = OracleStatusCode.GET_USER_CONNECTION
            conn = self.create_connection(user, passwd)

            conn.callTimeout = int(os.environ['ORACLE_STMT_TIMEOUT_MS'])
            state = OracleStatusCode.EXECUTE_CREATE
            execute_sql_script(conn, creation)

            state = OracleStatusCode.EXECUTE_INSERT
            execute_sql_script(conn, insertion)

            db = None
            if pre_db:
                state = OracleStatusCode.GET_ALL_TABLES
                db = get_all_tables(conn)

            state = OracleStatusCode.EXECUTE_USER_CODE
            init = time.time()

            # sqlparse does not consider the whole CREATE PROCEDURE as a single statement, so we cannot check
            # the minimum and maximum number of statements in this kind of problems :-(

            with conn.cursor() as cursor:
                stmt = proc_creation
                cursor.execute(stmt)

                # Stops if there is some compilation error in the procedure
                # We must handle it manually because executing a PROCEDURE creation with failures does not throw
                # any Oracle exception
                errors = get_compilation_errors(conn)
                if len(errors['rows']) > 0:
                    raise ExecutorException(OracleStatusCode.COMPILATION_ERROR, message=errors, statement=stmt)

                stmt = f"BEGIN {proc_call.strip()}; END;"
                cursor.execute(stmt)

            state = OracleStatusCode.GET_ALL_TABLES
            post = get_all_tables(conn)

            logger.debug('User %s - Procedure creation and testing executed in %s seconds',
                         conn.username, time.time() - init)

            state = OracleStatusCode.CLOSE_USER_CONNECTION
            conn.close()
            conn = None

            state = OracleStatusCode.DROP_USER
            self.drop_user(user, gestor)
            user = None

            state = OracleStatusCode.RELEASE_ADMIN_CONNECTION
            self.connection_pool.release(gestor)
            gestor = None

            return {'pre': db, 'post': post}
        except cx_Oracle.DatabaseError as excp:
            error_msg = str(excp)
            logger.info('Error when testing procedure creation and call: %s - %s - %s', state, excp, stmt)
            if ('ORA-3156' in error_msg or 'ORA-24300' in error_msg) and state == OracleStatusCode.EXECUTE_USER_CODE:
                # Time limit exceeded
                raise ExecutorException(OracleStatusCode.TLE_USER_CODE, error_msg, stmt) from excp
            raise ExecutorException(state, error_msg, stmt) from excp
        finally:
            if conn:
                conn.close()
            if user:
                try:
                    # Sometimes when TLE, the connections can be closed but the user cannot be dropped because
                    # "is currently connected". This looks like a bug or undocumented behavior of cx_Oracle
                    # These users must be removed manually later
                    self.drop_user(user, gestor)
                except cx_Oracle.DatabaseError as drop_except:  # pragma: no cover
                    logger.error('Unable to drop user %s, REMOVE IT MANUALLY (%s)', user, drop_except)
            if gestor:
                self.connection_pool.release(gestor)

    def execute_trigger_test(self, creation, insertion, trigger_definition, tests, pre_db=True):
        """
        Using a new fresh user, creates a set of tables ('creation) and inserts some data.
        Then, creates a PROCEDURE defined in proc_creation and invokes the call in proc_call
        :param pre_db:
        :param tests: (str) 1 or more DML statements that should invoke the trigger
        :param trigger_definition:
        :param creation: (str) Statements to create the tables and other structures
        :param insertion: (str) Statements to insert data into tables

        :return: {'pre': DB, 'post': DB} dictionary containing the state of the DB before defining the trigger and
                   and after executing the tests
        """
        conn, gestor, user, post, stmt = None, None, None, None, None
        state = OracleStatusCode.GET_ADMIN_CONNECTION
        try:
            gestor = self.connection_pool.acquire()

            state = OracleStatusCode.CREATE_USER
            user, passwd = self.create_user(gestor)

            state = OracleStatusCode.GET_USER_CONNECTION
            conn = self.create_connection(user, passwd)

            conn.callTimeout = int(os.environ['ORACLE_STMT_TIMEOUT_MS'])
            state = OracleStatusCode.EXECUTE_CREATE
            execute_sql_script(conn, creation)

            state = OracleStatusCode.EXECUTE_INSERT
            execute_sql_script(conn, insertion)

            db = None
            if pre_db:
                state = OracleStatusCode.GET_ALL_TABLES
                db = get_all_tables(conn)

            state = OracleStatusCode.EXECUTE_USER_CODE
            init = time.time()

            # sqlparse does not consider the whole CREATE TRIGGER as a single statement, so we cannot check
            # the minimum and maximum number of statements in this kind of problems :-(

            with conn.cursor() as cursor:
                stmt = trigger_definition
                cursor.execute(stmt)
            # cx_Oracle does not seem to compile trigger at this point. Syntax error in the trigger will be detected
            # when firing the trigger

            execute_dml_statements(conn, tests)

            state = OracleStatusCode.GET_ALL_TABLES
            post = get_all_tables(conn)

            logger.debug('User %s - Procedure creation and testing executed in %s seconds',
                         conn.username, time.time() - init)

            state = OracleStatusCode.CLOSE_USER_CONNECTION
            conn.close()
            conn = None

            state = OracleStatusCode.DROP_USER
            self.drop_user(user, gestor)
            user = None

            state = OracleStatusCode.RELEASE_ADMIN_CONNECTION
            self.connection_pool.release(gestor)
            gestor = None

            return {'pre': db, 'post': post}
        except cx_Oracle.DatabaseError as excp:
            error_msg = str(excp)
            logger.info('Error when testing trigger creation and call: %s - %s - %s', state, excp, stmt)
            if ('ORA-3156' in error_msg or 'ORA-24300' in error_msg) and state == OracleStatusCode.EXECUTE_USER_CODE:
                # Time limit exceeded
                raise ExecutorException(OracleStatusCode.TLE_USER_CODE, error_msg, stmt) from excp
            if 'ORA-04098' in error_msg:
                # trigger is invalid and failed re-validation => compilation error
                errors = get_compilation_errors(conn)
                raise ExecutorException(OracleStatusCode.COMPILATION_ERROR, message=errors, statement=stmt) from excp
            raise ExecutorException(state, error_msg, stmt) from excp
        finally:
            if conn:
                conn.close()
            if user:
                try:
                    # Sometimes when TLE, the connections can be closed but the user cannot be dropped because
                    # "is currently connected". This looks like a bug or undocumented behavior of cx_Oracle
                    # These users must be removed manually later
                    self.drop_user(user, gestor)
                except cx_Oracle.DatabaseError as drop_except:  # pragma: no cover
                    logger.error('Unable to drop user %s, REMOVE IT MANUALLY (%s)', user, drop_except)
            if gestor:
                self.connection_pool.release(gestor)

    def execute_discriminant_test(self, creation, insertion_base, insertion_user, select_correct, select_incorrect):
        """
        Using a new fresh user, creates a set of tables (creation) and inserts some data: the base INSERT sentences
        and also the INSERT sentences from the user. Then, executes a correct and wrong SELECT statements, returning
        both results in a dictionary
        :param creation: (str) Statements to create the tables and other structures
        :param insertion_base: (str) Statements to insert data into tables from the program definition
        :param insertion_user: (str) Statements to insert data into tables from the user submission
        :param select_correct: (str) One SELECT statement to execute that returns correct results
        :param select_incorrect: (str) One SELECT statement to execute that returns incorreect results
        :return: {"result_correct": result, "result_wrong": result}. 'result' is a dictionary representing the
                 statement result of a query (in this case, select_correct and select_incorrect)
                 In case of error, throws a ExecutorException
        """
        conn, gestor, result_correct, result_incorrect, user = None, None, None, None, None
        state = OracleStatusCode.GET_ADMIN_CONNECTION
        try:
            gestor = self.connection_pool.acquire()

            state = OracleStatusCode.CREATE_USER
            user, passwd = self.create_user(gestor)

            state = OracleStatusCode.GET_USER_CONNECTION
            conn = self.create_connection(user, passwd)

            conn.callTimeout = int(os.environ['ORACLE_STMT_TIMEOUT_MS'])
            state = OracleStatusCode.EXECUTE_CREATE
            execute_sql_script(conn, creation)

            state = OracleStatusCode.EXECUTE_INSERT
            execute_sql_script(conn, insertion_base)

            state = OracleStatusCode.EXECUTE_USER_CODE
            execute_sql_script(conn, insertion_user)

            state = OracleStatusCode.EXECUTE_DISCRIMINANT_SELECT
            result_correct = execute_select_statement(conn, select_correct)

            state = OracleStatusCode.EXECUTE_DISCRIMINANT_SELECT
            result_incorrect = execute_select_statement(conn, select_incorrect)

            state = OracleStatusCode.CLOSE_USER_CONNECTION
            conn.close()
            conn = None

            state = OracleStatusCode.DROP_USER
            self.drop_user(user, gestor)
            user = None

            state = OracleStatusCode.RELEASE_ADMIN_CONNECTION
            self.connection_pool.release(gestor)
            gestor = None
            return {"result_correct": result_correct, "result_incorrect": result_incorrect}
        except cx_Oracle.DatabaseError as excp:
            error_msg = str(excp)
            logger.info('Error when testing DISCRIMINANT problem: %s - %s - %s - %s - %s', state, excp, insertion_user,
                        select_correct, select_incorrect)
            if 'ORA-3156' in error_msg or 'ORA-24300' in error_msg:
                # Time limit exceeded
                raise ExecutorException(OracleStatusCode.TLE_USER_CODE, error_msg,
                                        (insertion_user, select_correct, select_incorrect)) from excp
            # Errors can only happen in user code, i.e., insertion_user
            pos = line_col_from_offset(insertion_user, offset_from_oracle_exception(excp))
            raise ExecutorException(state, error_msg, insertion_user, pos) from excp
        finally:
            if conn:
                conn.close()
            if user:
                try:
                    # Sometimes when TLE, the connections can be closed but the user cannot be dropped because
                    # "is currently connected". This looks like a bug or undocumented behavior of cx_Oracle
                    # These users must be removed manually later
                    self.drop_user(user, gestor)
                except cx_Oracle.DatabaseError as drop_except:  # pragma: no cover
                    logger.error('Unable to drop user %s, REMOVE IT MANUALLY (%s)', user, drop_except)
            if gestor:
                self.connection_pool.release(gestor)
