from django.urls import path
from api import views, views_frontend
from django.contrib.auth import views as auth_views, login
from django.conf import settings
from django.conf.urls.static import static
from api.views import custom_logout, upload_participants

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
    path('logout/', custom_logout, name='logout'),
    path('event/<int:event_id>/add_results/', views.add_event_results, name='add_event_results'),
    path('event/<int:event_id>/upload_photos/', views.upload_event_photos, name='upload_event_photos'),
    path('send-email-to-paid/<int:event_id>/', views.send_email_to_paid, name='send_email_to_paid'),
    path('event/<int:event_id>/upload/', views.upload_participants, name='upload_participants'),

    # Front-end URLs
    path('events-front/', views_frontend.event_list, name='events'),
    path('register-participant/<int:event_id>', views_frontend.participant_register, name='register_participant'),
    path('participant-list/<int:event_id>', views_frontend.participant_list, name='participants_front'),
    path('event/<int:event_id>/photos/', views_frontend.event_photos, name='event_photos'),
    path('results/<int:event_id>/', views.show_results, name='show_results'),
    path('payment-options/<int:participant_id>/<int:event_id>/<int:selected_distance>/',views_frontend.payment_options,name='payment_options'),
    path('payment-success/<int:participant_id>/', views_frontend.payment_success, name='payment_success'),
    path('payment-pending/<int:participant_id>/', views_frontend.payment_pending, name='payment_pending'),
    path('apie-mus/', views_frontend.about_us, name='about_us'),
    path('privatumo-politika/', views_frontend.privacy_policy, name='privacy_policy'),
    path('kontaktai/', views_frontend.contact, name='contact'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)