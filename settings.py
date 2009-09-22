# Django settings for newscredit_store project.
import os

# Default logging level
LOG_TO_FILE = False
LOG_LEVEL = None
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])

# If you set this to False, Django will make some optimizations so as 
# not to load the internationalization machinery.
USE_I18N = True

# List of callables that know how to import templates from various 
# sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'urls'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.databrowse',
    'crawler',
    'entify',
    'solango',
    'tagging',
    'django_extensions',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or 
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

SEARCH_FACET_PARAMS = [
    ("facet", "true"),             # basic faceting
    ("facet.field", "author"),
    ("facet.field", "tags"),    
    ("facet.field", "people"),
]

SEARCH_SORT_PARAMS = {
    "score desc": "Relevance",
    "date desc" : "Date (desc)",
    "date asc" : "Date (asc)",
}

from localsettings import *