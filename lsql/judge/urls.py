from django.urls import path

from . import views

app_name = 'judge'
urlpatterns = [
    path('', views.index, name='index'),
    path('collection', views.AllCollectionsView.as_view(), name='collections'),
    path('collection/<int:pk>', views.CollectionView.as_view(), name='collection')
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]