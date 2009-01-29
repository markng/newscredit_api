from django.db import models
from django.contrib import admin, databrowse
from newscredit_store.locallibs.aump import hall, hatom
from tagging.fields import TagField
from tagging.models import Tag
import pprint

# Create your models here.
class CrawlSite(models.Model):
  """site from which we are crawling"""
  url = models.URLField("Site URL")
  name = models.TextField("Site Name", null=True, blank=True)
  def __unicode__(self):
    """string rep"""
    return self.url
  def crawl(self):
    #if we have no feed pages, add the actual url of the site itself
    if len(self.feed_pages.all()) < 1:
      feedpage = self.feed_pages.model()
      feedpage.url = self.url
      self.feed_pages.add(feedpage)
      return feedpage.fetch()
    else:
      results=[]
      for page in self.feed_pages.all():
        results.append(page.fetch())
      return results
admin.site.register(CrawlSite)
databrowse.site.register(CrawlSite)

class Article(models.Model):
  """article"""
  bookmark = models.URLField("Article permalink", unique=True)
  entry_title = models.TextField("Title", null=True, blank=True)
  entry_content = models.TextField("Content", null=True, blank=True)
  entry_summary = models.TextField("Summary", null=True, blank=True)
  updated = models.DateTimeField("Last Updated", null=True, blank=True)
  published = models.DateTimeField("First Published", null=True, blank=True)
  tags = TagField()
  def __unicode__(self):
    """string rep"""
    return(self.entry_title)
  def set_tags(self, tags):
    Tag.objects.update_tags(self, tags)
  def get_tags(self):
    return Tag.objects.get_for_object(self)
admin.site.register(Article)
databrowse.site.register(Article)

class FeedPage(models.Model):
  """pages which are either atom feeds or hatom pages"""
  url = models.URLField("Feed URL")
  crawl_site = models.ForeignKey(CrawlSite, related_name='feed_pages')
  def __unicode__(self):
    """string rep"""
    return self.url
  def fetch(self):
    """fetch feed and parse it"""
    parser = hatom.MicroformatHAtom(page_uri=self.url)
    results = [result for result in parser.Iterate()]
    # create articles and/or revision from results
    for result in results:
      pprint.pprint(result)
      article, created = Article.objects.get_or_create(bookmark=result.get('bookmark'))
      article.entry_title = result.get('entry-title')
      article.entry_content = result.get('entry-content')
      article.entry_summary = result.get('entry-summary')
      article.save()
    return True
admin.site.register(FeedPage)
databrowse.site.register(FeedPage)

class Author(models.Model):
  """article author"""
  fn = models.TextField("formatted name")
  nickname = models.TextField("nickname", blank=True, null=True)
  url = models.URLField("Author page")
  articles = models.ManyToManyField(Article, related_name='authors', through='WorkedOn')
admin.site.register(Author)
databrowse.site.register(Author)

class WorkedOn(models.Model):
  """relationship between articles and authors"""
  author = models.ForeignKey(Author)
  article = models.ForeignKey(Article)
  role = models.TextField(null=True, blank=True)
  class Meta:
    verbose_name = 'worked on (article <-> author)'
    verbose_name_plural = 'worked on (article <-> author)'

class Principles(models.Model):
  """principles"""
  url = models.URLField(unique=True)
  articles = models.ManyToManyField(Article, related_name='principles')
  class Meta:
    verbose_name_plural = 'Principles'
  
class Revision(models.Model):
  """revision of article"""
  article = models.ForeignKey("Article")
  source = models.URLField("Revision source URL")
  entry_title = models.TextField("Title")
  entry_content = models.TextField("Content", null=True, blank=True)
  entry_summary = models.TextField("Summary")
admin.site.register(Revision)