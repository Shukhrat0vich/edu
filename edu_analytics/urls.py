"""
Main URL configuration for EduAnalytics project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


urlpatterns = [

    # homepage → login page
    path('', lambda request: redirect('/login/')),

    # Django admin
    path('admin/', admin.site.urls),

    # Authentication
    path('', include('apps.users.urls')),

    # Dashboard
    path('dashboard/', include('apps.dashboard.urls')),

    # Analytics
    path('analytics/', include('apps.analytics.urls')),

    # API
    path('api/', include('apps.api.urls')),
]


# Media & static files (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)