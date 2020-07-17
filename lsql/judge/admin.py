from django.contrib import admin

from . import forms
from .models import Collection, SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem

# Register your models here.


# Customize how to show add/edit forms for problems
class SelectProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']
    form = forms.SelectProblemAdminForm


class DMLProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']
    form = forms.DMLProblemAdminForm


class FunctionProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'calls']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']
    form = forms.FunctionProblemAdminForm


class FunctionProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'proc_call']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']
    form = forms.ProcProblemAdminForm


class TriggerProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'tests']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']
    form = forms.TriggerProblemAdminForm


admin.site.register(Collection)
admin.site.register(SelectProblem, SelectProblemAdmin)
admin.site.register(DMLProblem, DMLProblemAdmin)
admin.site.register(FunctionProblem, FunctionProblemAdmin)
admin.site.register(ProcProblem, FunctionProblemAdmin)
admin.site.register(TriggerProblem, TriggerProblemAdmin)
