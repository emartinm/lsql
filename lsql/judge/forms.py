from django import forms


class SelectProblemAdminForm(forms.ModelForm):
    create_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    insert_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    text_md = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))


class DMLProblemAdminForm(forms.ModelForm):
    create_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    insert_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    text_md = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))


class FunctionProblemAdminForm(forms.ModelForm):
    create_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    insert_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    text_md = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    calls = forms.CharField(label='List of function calls to test (one per line)',
                            widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))


class ProcProblemAdminForm(forms.ModelForm):
    create_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    insert_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    text_md = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    proc_call = forms.CharField(label='Procedure call to test (only one)',
                                widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))


class TriggerProblemAdminForm(forms.ModelForm):
    create_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    insert_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    text_md = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    tests = forms.CharField(label='SQL statements to test the trigger (separated by ";" as usual)',
                            widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))


class LoginForm(forms.Form):
    username = forms.CharField(label='Nombre de usuario', max_length=100)
    password = forms.CharField(label='Contraseña', max_length=100, widget=forms.PasswordInput)


class SubmitForm(forms.Form):
    code = forms.CharField(label='Codigo', min_length=10)
