from django.urls import path

from . import views

app_name = 'judge'
urlpatterns = [
    path('', views.index, name='index'),
    path('collection', views.collections, name='collections'),
    path('collection/<int:pk>', views.collection, name='collection'),
    path('user/<int:pk>', views.user, name='user'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout')
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]