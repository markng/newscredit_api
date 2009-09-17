from os import path as os_path

from django.conf.urls.defaults import *
from django.contrib import admin, databrowse
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^databrowse/(.*)', databrowse.site.root),
    (r'^$', 'django.views.generic.simple.direct_to_template', {'template' : 'index.html'}, 'home'),
    (r'^images/(.*)$', 'django.views.static.serve', {'document_root': os_path.join(settings.PROJECT_PATH, 'media/images')}, 'images'),
    (r'^css/(.*)$', 'django.views.static.serve', {'document_root': os_path.join(settings.PROJECT_PATH, 'media/css')}),
    (r'^js/(.*)$', 'django.views.static.serve', {'document_root': os_path.join(settings.PROJECT_PATH, 'media/js')}),
    (r'^search/', include('solango.urls')),
    url(r'^search.json/$', 'solango.views.select', {'template_name' : 'json.html'}, 'solango_search_json'),
    (r'^', include('crawler.urls')),
)
