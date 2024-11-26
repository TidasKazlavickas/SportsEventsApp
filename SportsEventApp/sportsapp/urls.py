from django.urls import path
from api import views

urlpatterns = [
    path('', views.index, name='index'),  # Frontend view
    path('one/', views.event_list, name='return-one'),  # Existing views
    path('two/', views.return_two, name='return-two'),
    path('sum/', views.sum_numbers, name='sum-numbers'),
    path('db-health/', views.db_health_check, name='db_health_check'),
    path('renginiai/', views.event_list, name='event_list'),
    path('create-event/', views.create_event, name='create_event'),
]
