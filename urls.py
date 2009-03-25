from django.conf.urls.defaults import *
from django.contrib import admin, databrowse

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^newscredit_store/', include('newscredit_store.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    (r'^databrowse/(.*)', databrowse.site.root),
    (r'^$', 'django.views.generic.simple.direct_to_template', {'template' : 'index.html'}, 'home'),
    (r'^search/', include('solango.urls')),
    (r'^', include('crawler.urls')),
)
