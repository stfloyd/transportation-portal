from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from transportation import models


UserAdmin.list_display += ('is_moderator', 'is_driver')
UserAdmin.list_filter += ('is_moderator', 'is_driver')
UserAdmin.fieldsets = (
    (None, {'fields': ('username', 'password')}),
    ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
    ('Permissions', {'fields': ('is_active', 'is_driver', 'is_moderator',
                                'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    ('Important dates', {'fields': ('last_login', 'date_joined')})
)

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Organization)
admin.site.register(models.Budget)
admin.site.register(models.Department)
admin.site.register(models.TripRequest)
admin.site.register(models.TripRequestActivity)
admin.site.register(models.Driver)
admin.site.register(models.Vehicle)
admin.site.register(models.VehicleActivity)
admin.site.register(models.VehicleMaintenance)
admin.site.register(models.Setting)
