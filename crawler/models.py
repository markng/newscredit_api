from django.db import models

# Create your models here.
class CrawlSite(models.Model):
  """site from which we are crawling"""
  url = models.URLField("Site URL")
  feed_url = models.URLField("site rss/atom feed")
