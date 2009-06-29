from django.contrib import admin, databrowse
from models import *

databrowse.site.register(Person)
admin.site.register(Person)
databrowse.site.register(Organisation)
admin.site.register(Organisation)
databrowse.site.register(Place)
admin.site.register(Place)