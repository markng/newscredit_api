from django.conf.urls.defaults import *
from django.contrib import admin, databrowse

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^databrowse/(.*)', databrowse.site.root),
    (r'^$', 'django.views.generic.simple.direct_to_template', {'template' : 'index.html'}, 'home'),
    (r'^search/', include('solango.urls')),
    url(r'^search.json/$', 'solango.views.select', {'template_name' : 'json.html'}, 'solango_search_json'),
    (r'^', include('crawler.urls')),
)
