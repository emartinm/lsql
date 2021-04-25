# -*- coding: utf-8 -*-
"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Mapping from URL to views
"""

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = 'judge'
urlpatterns = [
    path('', views.index, name='index'),
    path('help/', views.help_page, name='help'),
    path('collection/', views.show_collections, name='collections'),
    path('collection/<int:collection_id>', views.show_collection, name='collection'),
    path('problem/<int:problem_id>', views.show_problem, name='problem'),
    path('submit/<int:problem_id>', views.submit, name='submit'),
    path('problem/<int:problem_id>/create_insert', views.download, name='create_insert'),
    path('submission/', views.show_submissions, name='submissions'),
    path('submission/<int:submission_id>', views.show_submission, name='submission'),
    path('submission/<int:submission_id>/download_submission', views.download_submission, name='download_submission'),
    path('results/', views.show_results, name='results'),
    path('results/<int:collection_id>', views.show_result, name='result'),
    path('results/<int:collection_id>/download_ranking', views.download_ranking, name='download_ranking'),
    path('achievements/<int:user_id>', views.show_achievements, name='achievements'),
    path('statistics/submissions', views.statistics_submissions, name='statistics_submissions'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('password_change/',
         auth_views.PasswordChangeView.as_view(
             template_name='password_change.html',
             success_url=reverse_lazy('judge:password_change_done')
             # Using reverse() causes a cyclic import that breaks the system -> reverse_lazy
         ),
         name='password_change'
         ),
    path('password_change_done/', views.password_change_done, name='password_change_done'),
    path('test_error_500/', views.test_error_500, name='test_error_500'),
]
