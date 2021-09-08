# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Customize how to show add/edit forms for objects in the Admin
"""

from django.contrib import admin

from . import forms
from .models import Collection, SelectProblem, DMLProblem, FunctionProblem, ProcProblem, TriggerProblem, \
    Submission, NumSolvedCollectionAchievementDefinition, PodiumAchievementDefinition, \
    NumSolvedAchievementDefinition, ObtainedAchievement, DiscriminantProblem, NumSolvedTypeAchievementDefinition, \
    NumSubmissionsProblemsAchievementDefinition, Hint, UsedHint


class SelectProblemAdmin(admin.ModelAdmin):
    """Model for SelectProblem, hides author when editing because the current user will be used """
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('pk', 'title_md', 'creation_date', 'collection', 'author')
    list_filter = ['collection', 'creation_date']

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class DMLProblemAdmin(admin.ModelAdmin):
    """Model for DMLProblem, hides author when editing because the current user will be used """
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution']}),
    ]
    list_display = ('pk', 'title_md', 'creation_date', 'collection', 'author')
    list_filter = ['collection', 'creation_date']

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class FunctionProblemAdmin(admin.ModelAdmin):
    """Model for FunctionProblem, hides author when editing because the current user will be used """
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'calls']}),
    ]
    list_display = ('pk', 'title_md', 'creation_date', 'collection', 'author')
    list_filter = ['collection', 'creation_date']
    form = forms.FunctionProblemAdminForm

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class ProcProblemAdmin(admin.ModelAdmin):
    """Model for ProcProblem, hides author when editing because the current user will be used """
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'proc_call']}),
    ]
    list_display = ('pk', 'title_md', 'creation_date', 'collection', 'author')
    list_filter = ['collection', 'creation_date']
    form = forms.ProcProblemAdminForm

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class TriggerProblemAdmin(admin.ModelAdmin):
    """Model for TriggerProblem, hides author when editing because the current user will be used """
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'solution', 'tests']}),
    ]
    list_display = ('pk', 'title_md', 'creation_date', 'collection', 'author')
    list_filter = ['collection', 'creation_date']
    form = forms.TriggerProblemAdminForm

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class DiscriminantProblemAdmin(admin.ModelAdmin):
    """Model for FunctionProblem, hides author when editing because the current user will be used """
    fieldsets = [
        ('ZIP file (if present, it will overwrite the rest of fields)', {'fields': ['zipfile']}),
        ('Basic Information', {'fields': ['language', 'title_md', 'text_md', 'min_stmt', 'max_stmt', 'collection',
                                          'position', 'check_order']}),
        ('SQL', {'fields': ['create_sql', 'insert_sql', 'correct_query', 'incorrect_query']}),
    ]
    list_display = ('pk', 'title_md', 'creation_date', 'collection', 'author')
    list_filter = ['collection', 'creation_date']

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class CollectionAdmin(admin.ModelAdmin):
    """Model for Collection, hides author when editing because the current user will be used """
    # define get_fieldsets(self, request, obj=None) to have a dynamic behavior
    fieldsets = [
        ('If provided, loads problems from ZIP file and add them to the collection',
         {'fields': ('zipfile', )}),
        ('Collection data', {'fields': ('name_md', 'position', 'description_md', 'visible')})
    ]
    list_display = ('pk', 'name_md', 'creation_date', 'author', 'visible')
    list_filter = ['creation_date']

    def save_model(self, request, obj, form, change):
        """ When saving the collection using the admin interface, set the author to the current user
            if it is not already set
        """
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)

class SubmissionAdmin(admin.ModelAdmin):
    """Model for Submission"""
    list_display = ('pk', 'user', 'problem', 'verdict_code', 'creation_date')
    list_filter = ['creation_date', 'verdict_code', 'user']


# class ProblemAdmin(admin.ModelAdmin):
#     """Model for Problem"""
#     list_display = ('title_md', 'creation_date', 'collection')
#     list_filter = ['collection', 'creation_date']


# class AchievementsAdmin(admin.ModelAdmin):
#     """Model for Achievements"""
#     list_display = ('name', 'description')


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
    list_display = ('user', 'hint_definition', 'request_date')
    list_display_links = ('user', 'hint_definition')
    list_filter = ['user']


admin.site.register(Collection, CollectionAdmin)
# admin.site.register(Problem, ProblemAdmin)
admin.site.register(SelectProblem, SelectProblemAdmin)
admin.site.register(DMLProblem, DMLProblemAdmin)
admin.site.register(FunctionProblem, FunctionProblemAdmin)
admin.site.register(ProcProblem, ProcProblemAdmin)
admin.site.register(TriggerProblem, TriggerProblemAdmin)
admin.site.register(Submission, SubmissionAdmin)
# admin.site.register(AchievementDefinition, AchievementsAdmin)
admin.site.register(NumSolvedCollectionAchievementDefinition, NumSolvedCollectionAchievementDefinitionAdmin)
admin.site.register(PodiumAchievementDefinition, PodiumAchievementDefinitionAdmin)
admin.site.register(NumSolvedAchievementDefinition, NumSolvedAchievementDefinitionAdmin)
admin.site.register(ObtainedAchievement, ObtainedAchievementAdmin)
admin.site.register(DiscriminantProblem, DiscriminantProblemAdmin)
admin.site.register(NumSolvedTypeAchievementDefinition, NumSolvedTypeAchievementDefinitionAdmin)
admin.site.register(NumSubmissionsProblemsAchievementDefinition, NumSubmissionsProblemsAchievementDefinitionAdmin)
admin.site.register(Hint, HintAdmin)
admin.site.register(UsedHint, UsedHintAdmin)
