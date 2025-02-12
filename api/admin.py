from django.contrib import admin
from .models import Event, Participant, Group, Distance
from .admin_custom import CustomAdminSite

custom_admin_site = CustomAdminSite(name='custom_admin')

# Register models with the custom admin site
@admin.register(Event, site=custom_admin_site)
class EventAdmin(admin.ModelAdmin):
    pass

@admin.register(Participant, site=custom_admin_site)
class ParticipantAdmin(admin.ModelAdmin):
    pass

@admin.register(Group, site=custom_admin_site)
class GroupAdmin(admin.ModelAdmin):
    pass

@admin.register(Distance, site=custom_admin_site)
class DistanceAdmin(admin.ModelAdmin):
    pass