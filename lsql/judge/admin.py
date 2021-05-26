# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Customize how to show add/edit forms for objects in the Admin
"""

from django.contrib import admin

from . import forms
from .models import Collection, SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem, Problem, \
    Submission, AchievementDefinition, NumSolvedCollectionAchievementDefinition, PodiumAchievementDefinition, \
    NumSolvedAchievementDefinition, ObtainedAchievement, DiscriminantProblem, NumSolvedTypeAchievementDefinition, \
    NumSubmissionsProblemsAchievementDefinition, Hint, UsedHint


class SelectProblemAdmin(admin.ModelAdmin):
    """Model for SelectProblem"""
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'author', 'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']


class DMLProblemAdmin(admin.ModelAdmin):
    """Model for DMLProblem"""
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'author', 'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']


class FunctionProblemAdmin(admin.ModelAdmin):
    """Model for FunctionProblem"""
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'author', 'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'calls']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']
    form = forms.FunctionProblemAdminForm


class ProcProblemAdmin(admin.ModelAdmin):
    """Model for ProcProblem"""
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'author', 'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'proc_call']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']
    form = forms.ProcProblemAdminForm


class TriggerProblemAdmin(admin.ModelAdmin):
    """Model for TriggerProblem"""
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'author', 'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'tests']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']
    form = forms.TriggerProblemAdminForm


class DiscriminantProblemAdmin(admin.ModelAdmin):
    """Model for FunctionProblem"""
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'author', 'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'correct_query', 'incorrect_query']}),
    ]
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']


class CollectionAdmin(admin.ModelAdmin):
    """Model for Collection"""
    # define get_fieldsets(self, request, obj=None) to have a dynamic behavior
    fieldsets = [
        ('Load problems from ZIP (only if the collection exists). The new problems will be added',
         {'fields': ('zipfile', )}),
        ('Collection data', {'fields': ('name_md', 'position', 'description_md', 'author')})
    ]
    list_display = ('name_md', 'author', 'creation_date')
    list_filter = ['creation_date']


class SubmissionAdmin(admin.ModelAdmin):
    """Model for Submission"""
    list_display = ('pk', 'user', 'problem', 'veredict_code', 'creation_date')
    list_filter = ['creation_date', 'veredict_code', 'user']


class ProblemAdmin(admin.ModelAdmin):
    """Model for Problem"""
    list_display = ('title_md', 'creation_date', 'collection')
    list_filter = ['collection', 'creation_date']


class AchievementsAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('name', 'description')


class NumSolvedCollectionAchievementDefinitionAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('name', 'description', 'num_problems', 'collection')


class PodiumAchievementDefinitionAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('name', 'description', 'num_problems', 'position')


class NumSolvedAchievementDefinitionAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('name', 'description', 'num_problems')


class ObtainedAchievementAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('user', 'achievement_definition', 'obtained_date')
    list_filter = ['achievement_definition', 'obtained_date', 'user']


class NumSolvedTypeAchievementDefinitionAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('name', 'description', 'num_problems', 'problem_type')


class NumSubmissionsProblemsAchievementDefinitionAdmin(admin.ModelAdmin):
    """Model for Achievements"""
    list_display = ('name', 'description', 'num_problems', 'num_submissions')
    list_filter = ['name']


class HintAdmin(admin.ModelAdmin):
    """Model for Hints"""
    list_display = ('text_md', 'problem', 'num_submit')
    list_filter = ['problem']


class UsedHintAdmin(admin.ModelAdmin):
    """Model for Hints"""
    list_display = ('user', 'request_date', 'hint_definition')
    list_filter = ['user']


admin.site.register(Collection, CollectionAdmin)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(SelectProblem, SelectProblemAdmin)
admin.site.register(DMLProblem, DMLProblemAdmin)
admin.site.register(FunctionProblem, FunctionProblemAdmin)
admin.site.register(ProcProblem, ProcProblemAdmin)
admin.site.register(TriggerProblem, TriggerProblemAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(AchievementDefinition, AchievementsAdmin)
admin.site.register(NumSolvedCollectionAchievementDefinition, NumSolvedCollectionAchievementDefinitionAdmin)
admin.site.register(PodiumAchievementDefinition, PodiumAchievementDefinitionAdmin)
admin.site.register(NumSolvedAchievementDefinition, NumSolvedAchievementDefinitionAdmin)
admin.site.register(ObtainedAchievement, ObtainedAchievementAdmin)
admin.site.register(DiscriminantProblem, DiscriminantProblemAdmin)
admin.site.register(NumSolvedTypeAchievementDefinition, NumSolvedTypeAchievementDefinitionAdmin)
admin.site.register(NumSubmissionsProblemsAchievementDefinition, NumSubmissionsProblemsAchievementDefinitionAdmin)
admin.site.register(Hint, HintAdmin)
admin.site.register(UsedHint, UsedHintAdmin)
