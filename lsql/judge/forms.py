# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Forms used in LSQL
"""
from datetime import date
from django import forms
from django.core.exceptions import ValidationError


class FunctionProblemAdminForm(forms.ModelForm):
    """Customized form for FunctionProblem in admin to have a better label"""
    calls = forms.CharField(label='List of function calls to test (one per line)',
                            widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                            required=False)


class ProcProblemAdminForm(forms.ModelForm):
    """Customized form for ProcProblem in admin to have a better label"""
    proc_call = forms.CharField(label='Procedure call to test (only one)',
                                widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                                required=False)


class TriggerProblemAdminForm(forms.ModelForm):
    """Customized form for TriggerProblem in admin to have a better label"""
    tests = forms.CharField(label='SQL statements to test the trigger (separated by ";" as usual)',
                            widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                            required=False)


class LoginForm(forms.Form):
    """Form used to validate user login"""
    username = forms.CharField(label='Nombre de usuario', max_length=100)
    password = forms.CharField(label='Contraseña', max_length=100, widget=forms.PasswordInput)


class ResultForm(forms.Form):
    """Form used results"""
    group = forms.CharField(label='Grupo', max_length=20)
    start = forms.DateField(label='Desde', input_formats=['%Y-%m-%d'])
    end = forms.DateField(label='Hasta', input_formats=['%Y-%m-%d'])

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get("group")
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        if group is not None and not group.isdigit():
            raise ValidationError("El identificador de grupo no tiene el formato correcto")
        if end is None or start is None:
            raise ValidationError("Es necesario proporcionar tanto la fecha inicial como la fecha final.")
        if end is not None and start is not None:
            if end < start:
                raise ValidationError("¡Error! La fecha inicial no puede ser mayor que la fecha final.")
            if end > date.today():
                raise ValidationError("¡Error! La fecha final no puede ser mayor que la fecha de hoy.")
            if not isinstance(end, date) or not isinstance(start, date):
                raise ValidationError("Es necesario proporcionar tanto la fecha inicial como la fecha final.")
        return cleaned_data


class SubmitForm(forms.Form):
    """Form used to validate user submissions"""
    code = forms.CharField(label='Codigo', min_length=10)
