from django import forms


class SelectProblemAdminForm(forms.ModelForm):
    create_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    insert_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
    text_md = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}))
