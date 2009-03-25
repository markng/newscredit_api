# Django settings for newscredit_store project.
import os
from os import path as os_path
PROJECT_PATH = os_path.abspath(os_path.split(__file__)[0])

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'newscredit_store.urls'


INSTALLED_APPS = (
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.sites',
  'django.contrib.admin',
  'django.contrib.databrowse',
  'newscredit_store.crawler',
  'solango',
  'tagging',
  'extensions',
  'django_evolution',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os_path.join(PROJECT_PATH, 'templates'),
)

SEARCH_FACET_PARAMS = [
    ("facet", "true"),             # basic faceting
    ("facet.field", "author"),
]

SEARCH_SORT_PARAMS = {
        "score desc": "Relevance",
        "date desc" : "Date" # Added date
}

from localsettings import *