# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Forms used in LSQL
"""

from django import forms


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


class SubmitForm(forms.Form):
    """Form used to validate user submissions"""
    code = forms.CharField(label='Codigo', min_length=10)
