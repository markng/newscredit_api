from django.db import models
from django.contrib import admin

# Create your models here.
class CrawlSite(models.Model):
  """site from which we are crawling"""
  url = models.URLField("Site URL")
  name = models.TextField("Site Name", null=True, blank=True)
  def __unicode__(self):
    """string rep"""
    return self.url
admin.site.register(CrawlSite)

class FeedPages(models.Model):
  """pages which are either atom feeds or hatom pages"""
  url = models.URLField("Feed URL")
  crawl_site = models.ForeignKey(CrawlSite)

class Article(models.Model):
  """article"""
  bookmark = models.URLField("Article permalink", unique=True)
  entry_title = models.TextField("Title")
  entry_content = models.TextField("Content", null=True, blank=True)
  entry_summary = models.TextField("Summary")
  updated = models.DateTimeField("Last Updated", null=True, blank=True)
  published = models.DateTimeField("First Published", null=True, blank=True)
admin.site.register(Article)

class Author(models.Model):
  """article author"""
  fn = models.TextField("formatted name")
  nickname = models.TextField("nickname", blank=True, null=True)
  url = models.URLField("Author page")
  articles = models.ManyToManyField(Article, related_name='authors', through='WorkedOn')
admin.site.register(Author)

class WorkedOn(models.Model):
  """relationship between articles and authors"""
  author = models.ForeignKey(Author)
  article = models.ForeignKey(Article)
  role = models.TextField(null=True, blank=True)
  class Meta:
    verbose_name = 'worked on (article <-> author)'
    verbose_name_plural = 'worked on (article <-> author)'
admin.site.register(WorkedOn)
  
class Revision(models.Model):
  """revision of article"""
  article = models.ForeignKey("Article")
  source = models.URLField("Revision source URL")
  entry_title = models.TextField("Title")
  entry_content = models.TextField("Content", null=True, blank=True)
  entry_summary = models.TextField("Summary")
admin.site.register(Revision)

