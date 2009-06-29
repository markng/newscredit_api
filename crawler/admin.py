from django.contrib import admin, databrowse
from models import *

databrowse.site.register(Tag)
admin.site.register(CrawlSite)
databrowse.site.register(CrawlSite)
admin.site.register(FeedPage)
databrowse.site.register(FeedPage)
admin.site.register(Article)
databrowse.site.register(Article)
admin.site.register(Author)
databrowse.site.register(Author)
admin.site.register(Name)
databrowse.site.register(Name)
admin.site.register(Principles)
databrowse.site.register(Principles)
admin.site.register(Revision)
