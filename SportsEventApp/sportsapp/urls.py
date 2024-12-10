from django.urls import path
from api import views, views_frontend
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Back-end URLs
    path('', views.event_list, name='event_list'),
    path('create-event/', views.create_event, name='create_event'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/', views.event_list, name='event_list'),
    path('update-distances/', views.update_distances, name='update_distances'),
    path('participants/', views.participant_list, name='participant_list'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('edit-participant/<int:participant_id>/', views.edit_participant, name='edit_participant'),
    path('delete-participant/<int:participant_id>/', views.delete_participant, name='delete_participant'),
    path('event/<int:event_id>/export_participants_csv/', views.export_participants_csv, name='export_participants_csv'),
    path('event/<int:event_id>/export_all_participants_csv/', views.export_all_participants_csv, name='export_all_participants_csv'),
    path('event/<int:event_id>/add_participant/', views.add_participant, name='add_participant'),
    path('login/', auth_views.LoginView.as_view(template_name='api/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('event/<int:event_id>/add_results/', views.add_event_results, name='add_event_results'),
    path('event/<int:event_id>/upload_photos/', views.upload_event_photos, name='upload_event_photos'),
    path('send-email-to-paid/<int:event_id>/', views.send_email_to_paid, name='send_email_to_paid'),

    # Front-end URLs
    path('events-front/', views_frontend.event_list, name='events'),
    path('register-participant/<int:event_id>', views_frontend.participant_register, name='register_participant'),
    path('participant-list/<int:event_id>', views_frontend.participant_list, name='participants_front'),
    path('event/<int:event_id>/photos/', views_frontend.event_photos, name='event_photos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)