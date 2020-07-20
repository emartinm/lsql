from django import forms


class FunctionProblemAdminForm(forms.ModelForm):
    calls = forms.CharField(label='List of function calls to test (one per line)',
                            widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                            required=False)


class ProcProblemAdminForm(forms.ModelForm):
    proc_call = forms.CharField(label='Procedure call to test (only one)',
                                widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                                required=False)


class TriggerProblemAdminForm(forms.ModelForm):
    tests = forms.CharField(label='SQL statements to test the trigger (separated by ";" as usual)',
                            widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                            required=False)


class LoginForm(forms.Form):
    username = forms.CharField(label='Nombre de usuario', max_length=100)
    password = forms.CharField(label='Contraseña', max_length=100, widget=forms.PasswordInput)


class SubmitForm(forms.Form):
    code = forms.CharField(label='Codigo', min_length=10)
