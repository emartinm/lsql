# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Types used in LSQL
"""

from enum import IntEnum, unique
from django.db import models
from django.utils.translation import gettext_lazy as _


class VeredictCode(models.TextChoices):
    """Codes representing different judge veredicts"""
    AC = 'AC', _('Aceptado')
    TLE = 'TLE', _('Tiempo limite excedido')
    RE = 'RE', _('Error en ejecución')
    WA = 'WA', _('Resultados incorrectos')
    IE = 'IE', _('Error interno')
    VE = 'VE', _('Error de validación')

    def html_short_name(self):
        """Short name of the veredict code in HMTL with color"""
        if self == self.AC:
            return f'<span class="text-success">{self.label}</span>'
        return f'<span class ="text-danger">{self.label}</span>'

    def message(self):
        """Message to show in the modal window in the webpage"""
        if self == self.AC:
            return _('¡Enhorabuena! Tu código SQL ha generado los resultados esperados.')
        if self == self.TLE:
            return _('Puede deberse a una sobrecarga puntual del servidor, pero seguramente sea debido a que tu '
                     'código SQL no es suficientemente eficiente. Vuelve a enviarlo en unos minutos y si sigues '
                     'obteniendo el mismo veredicto trata de reescribir tu código lo para ser más eficiente.')
        if self == self.RE:
            return _('Tu código SQL ha producido un error durante la ejecución. Consulta el cuadro rojo en '
                     'la parte inferior de la página para ver los detalles.')
        if self == self.WA:
            return _('Tu código SQL ha generado resultados erróneos. Consulta el cuadro rojo en la parte inferior '
                     'de la página para ver los detalles.')
        if self == self.IE:
            return _('Error inesperado al ejecutar tu código. Por favor, inténtalo de nuevo.')
        return _('Error de validación de tu código.')  # self == self.VE:


@unique
class ProblemType(IntEnum):
    """Types of problems"""
    SELECT = 0
    DML = 1
    FUNCTION = 2
    PROC = 3
    TRIGGER = 4


@unique
class OracleStatusCode(IntEnum):
    """Status code returned by the DB executor"""
    OK = 0
    GET_ADMIN_CONNECTION = 1
    CREATE_USER = 2
    EXECUTE_CREATE = 3
    EXECUTE_INSERT = 4
    EXECUTE_USER_CODE = 5
    NUMBER_STATEMENTS = 6
    DROP_USER = 7
    RELEASE_ADMIN_CONNECTION = 8
    CLOSE_USER_CONNECTION = 9
    GET_USER_CONNECTION = 10
    OTHER = 11
    GET_ALL_TABLES = 12
    COMPILATION_ERROR = 13
    TLE_USER_CODE = 14
