"""

Transportation Portal URL Configuration

"""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('rest_framework_social_oauth2.urls')),
    path('', include('social_django.urls', namespace='social')),
    path('', include('transportation.urls'))

]
