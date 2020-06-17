from django.contrib import admin

from . import forms
from .models import Collection, SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem

# Register your models here.


class SelectProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']
    form = forms.SelectProblemAdminForm


admin.site.register(Collection)
admin.site.register(SelectProblem, SelectProblemAdmin)
admin.site.register(DMLProblem)
admin.site.register(FunctionProblem)
admin.site.register(ProcProblem)
admin.site.register(TriggerProblem)
