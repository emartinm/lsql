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
    path('collection/', views.collections, name='collections'),
    path('collection/<int:pk>', views.collection, name='collection'),
    path('problem/<int:pk>', views.problem, name='problem'),

    path('submit/<int:pk>', views.submit, name='submit'),

    path('submission/', views.submissions, name='submissions'),
    path('submission/<int:pk>', views.submission, name='submission'),

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
    path('password_change_done/', views.password_change_done, name='password_change_done')
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]
