from django.contrib import admin

from . import forms
from .models import Collection, SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem, Problem, \
    Submission


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


class DMLProblemAdmin(admin.ModelAdmin):
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection', 'author',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['creation_date']


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


class ProcProblemAdmin(admin.ModelAdmin):
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


class CollectionAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        # Only shows the ZIP file when the collection exists
        if obj is None:
            return [(None, {'fields': ('name_md', 'position', 'description_md', 'author')})]
        else:
            return [
                ('Load problems from ZIP (the new problems will be added)', {'fields': ('zipfile', )}),
                ('Collection data', {'fields': ('name_md', 'position', 'description_md', 'author')})
            ]

    list_display = ('name_md', 'author', 'creation_date')
    list_filter = ['creation_date']


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'problem', 'veredict_code', 'creation_date')
    list_filter = ['creation_date']


admin.site.register(Collection, CollectionAdmin)
admin.site.register(Problem)
admin.site.register(SelectProblem, SelectProblemAdmin)
admin.site.register(DMLProblem, DMLProblemAdmin)
admin.site.register(FunctionProblem, FunctionProblemAdmin)
admin.site.register(ProcProblem, ProcProblemAdmin)
admin.site.register(TriggerProblem, TriggerProblemAdmin)
admin.site.register(Submission, SubmissionAdmin)
