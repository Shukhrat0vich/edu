"""WSGI config for edu_analytics project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu_analytics.settings.dev')
application = get_wsgi_application()
