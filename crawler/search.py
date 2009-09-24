import datetime
import re
import solango

from crawler.models import Article

class ArticleDocument(solango.SearchDocument):
    date = solango.fields.DateField()
    title = solango.fields.CharField(copy=True)
    content = solango.fields.TextField(copy=True)
    author = solango.fields.CharField(copy=True, multi_valued=True)
    tags = solango.fields.CharField(copy=True, multi_valued=True)
    people = solango.fields.CharField(copy=True, multi_valued=True)
    organisations = solango.fields.CharField(copy=True,
        multi_valued=True)
    places = solango.fields.CharField(copy=True, multi_valued=True)
    _cached_model = False

    class Media:
        template = 'solango/document.html'

    def transform_date(self, instance):
        if instance.updated:
            return instance.updated
        elif instance.published:
            return instance.published
        else:
            return datetime.datetime.now()

    def transform_content(self, instance):
        r = re.compile(r'<.*?>') # strip html tags
        if instance.entry_content:
            return r.sub('', instance.entry_content)
        elif instance.entry_summary:
            return r.sub('', instance.entry_summary)
        else:
            return ''

    def transform_title(self, instance):
        if instance.entry_title:
            return instance.entry_title
        else:
            return instance.__unicode__()

    def transform_author(self, instance):
        """docstring for transform_author"""
        names = []
        for name in instance.names.all():
            names.append(str(name))
        return names

    def transform_tags(self, instance):
        """transform tags for solr"""
        return instance.tags.split(',')

    def transform_entity(self, instance, what):
        """get a model for solr"""
        whats = []
        for _what in instance.get_entity(what):
            whats.append(str(_what))
        return whats

    def transform_people(self, instance):
        """get people for solr"""
        return self.transform_entity(instance, 'Person')

    def transform_organisations(self, instance):
        """get organisations for solr"""
        return self.transform_entity(instance, 'Organisation')

    def transform_places(self, instance):
        """get places for solr"""
        return self.transform_entity(instance, 'Place')

    def get_model(self):
        """get model"""
        if not self._cached_model:
            self._cached_model = Article.objects.get(
                id=self.fields['id'].value
            )
        return self._cached_model

solango.register(Article, ArticleDocument)