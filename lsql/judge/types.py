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

    def message(self, problem=None):
        """Message to show in the modal window in the webpage"""
        msg = _('Error inesperado al ejecutar tu código. Por favor, inténtalo de nuevo.')
        if self == self.AC:
            msg = _('¡Enhorabuena! Tu código SQL ha generado los resultados esperados.')
        elif self == self.TLE:
            msg = _('Puede deberse a una sobrecarga puntual del servidor, pero seguramente sea debido a que tu '
                    'código SQL no es suficientemente eficiente. Vuelve a enviarlo en unos minutos y si sigues '
                    'obteniendo el mismo veredicto trata de reescribir tu código para ser más eficiente.')
        elif self == self.RE:
            msg = _('Tu código SQL ha producido un error durante la ejecución. Consulta el cuadro rojo '
                    'de retroalimentación en la parte inferior de la página para ver los detalles e inspecciona '
                    'el código resaltado en el editor.')
        elif self == self.WA:
            msg = _('Tu código SQL ha generado resultados erróneos. Consulta el cuadro rojo en la parte inferior '
                    'de la página para ver los detalles.')
        elif self == self.VE:
            msg = _('Comprueba que tu solución no está vacía, que la cantidad de sentencias SQL enviadas '
                    'es la adecuada y que estás enviando texto plano con letras del alfabeto inglés '
                    '(sin tildes).')
            if problem is not None and problem.min_stmt == problem.max_stmt:
                ending = "sentencias SQL" if problem.max_stmt > 1 else "sentencia SQL"
                msg = _(f'Se esperaba exactamente {problem.min_stmt} {ending}.')
            elif problem is not None:
                ending = "sentencias SQL" if problem.max_stmt > 1 else "sentencia SQL"
                msg = _(f'Tu envío debe estar formado por entre {problem.min_stmt} y {problem.max_stmt} {ending}.')

        return msg


@unique
class ProblemType(IntEnum):
    """Types of problems"""
    SELECT = 0
    DML = 1
    FUNCTION = 2
    PROC = 3
    TRIGGER = 4
    DISC = 5


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
    EXECUTE_DISCRIMINANT_SELECT = 15
