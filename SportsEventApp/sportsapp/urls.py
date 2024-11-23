from django.urls import path
from api import views

urlpatterns = [
    path('', views.index, name='index'),  # Frontend view
    path('one/', views.return_one, name='return-one'),  # Existing views
    path('two/', views.return_two, name='return-two'),
    path('sum/', views.sum_numbers, name='sum-numbers'),
    path('db-health/', views.db_health_check, name='db_health_check'),
]
