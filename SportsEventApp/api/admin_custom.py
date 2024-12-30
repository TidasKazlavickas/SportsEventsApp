from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse

class CustomAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        # If the user is authenticated and is an admin, redirect them
        if request.user.is_authenticated and request.user.is_staff:
            return redirect(reverse('event_list'))
        return super().login(request, extra_context)