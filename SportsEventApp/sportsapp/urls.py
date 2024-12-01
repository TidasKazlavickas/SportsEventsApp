from django.urls import path
from api import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create-event/', views.create_event, name='create_event'),
    path('events/', views.event_list, name='event_list'),
    path('register-participant/', views.register_participant, name='register_participant'),
    path('update-distances/', views.update_distances, name='update_distances'),  # for AJAX
]
