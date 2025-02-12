from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class CustomAdminSite(AdminSite):
    site_url = '/events/'  # Redirect "View Site" to the frontend events page
    site_header = _("Django Administravimas")  # Custom header text
    site_title = _("Sporto Renginiai Admin")  # Custom title text
    index_title = _("Tinklalapio administravimas")  # Dashboard index title

    def login(self, request, extra_context=None):
        # If the user is authenticated and is an admin, redirect them
        if request.user.is_authenticated and request.user.is_staff:
            return redirect(reverse('event_list'))
        return super().login(request, extra_context)

    def get_app_list(self, request):
        # Override to ensure the app list is properly displayed
        app_list = super().get_app_list(request)
        return app_list  # Ensure apps and models are displayed

