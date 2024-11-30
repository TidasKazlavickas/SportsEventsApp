from django.urls import path
from api import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-event/', views.create_event, name='create_event'),
]
