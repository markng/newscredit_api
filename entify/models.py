import base64
try:
    import cPickle as pickle
except:
    import pickle

from django.db import models


# serialized data field implementation shamelessly copied from http://www.davidcramer.net/code/181/custom-fields-in-django.html
class SerializedDataField(models.TextField):
    """Because Django for some reason feels its needed to repeatedly 
    call to_python even after it's been converted this does not support 
    strings."""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value is None:
            return
        if not isinstance(value, basestring):
            return value
        value = pickle.loads(base64.b64decode(value))
        return value

    def get_db_prep_save(self, value):
        if value is None:
            return
        return base64.b64encode(pickle.dumps(value))


# Create your models here.
class Person(models.Model):
    """a person"""
    name = models.TextField()
    role = models.CharField(null=True, blank=True, max_length=255)
    uri = models.URLField(unique=True)
    data = SerializedDataField(null=True, blank=True)
    source = models.CharField(null=True, blank=True, max_length=255)

    def __unicode__(self):
        """string rep for person"""
        return self.name

    def from_calais(self, entity):
        """populate from a calais entity"""
        entity = strip_calais_specifics(entity)
        self.uri = entity['__reference']
        self.name = entity['name']
        self.role = entity['persontype']
        self.source = 'calais'
        self.data = entity
        pass

class Organisation(models.Model):
    """an organization or company"""
    name = models.TextField()
    nationality = models.TextField()
    type = models.TextField()
    uri = models.URLField(unique=True)
    data = SerializedDataField(null=True,blank=True)
    source = models.CharField(null=True, blank=True, max_length=255)

    def __unicode__(self):
        """string rep for person"""
        return self.name

    def from_calais(self, entity):
        """populate from a calais entity"""
        entity = strip_calais_specifics(entity)
        self.uri = entity['__reference']
        self.name = entity['name']
        self.nationality = entity['nationality']
        try:
            self.type = entity['organizationtype']
        except KeyError:
            # companies don't have organizationtypes
            pass
        self.source = 'calais'
        self.data = entity
        pass

class Place(models.Model):
    """a city, country, continent, facility, region """
    name = models.TextField()
    uri = models.URLField(unique=True)
    data = SerializedDataField(null=True,blank=True)

    def __unicode__(self):
        """string rep for person"""
        return self.name

    def from_calais(self, entity):
        """populate from a calais entity"""
        entity = strip_calais_specifics(entity)
        self.uri = entity['__reference']
        self.name = entity['name']
        self.source = 'calais'
        self.data = entity
        pass

def strip_calais_specifics(entity):
    """strip specifics to an instance of an entity coming from calais"""
    del entity['instances']
    del entity['relevance']
    return entity

def analyze(model, text=None, backend='calais'):
    from calais import Calais
    from django.conf import settings

    calais = Calais(settings.CALAIS_API_KEY, submitter='newscredit')
    if not text:
        _text = model.analysis_text()
    else:
        _text = text

    # we cannot analyse if our total content is under 100 characters
    # after HTML cleaning. We leave OpenCalais to do this as they have
    # advanced heuristics to do it. If our text to analyse is less than
    # 100 characters, we skip the analysis.
    if len( _text ) < 100:
        return

    result = calais.analyze(_text)
    records = []

    try:
        for entity in result.entities:
            if entity['_type'] == 'Person':
                _model = Person
            elif entity['_type'] in [ 'City', 'Country', 'Continent',
                                        'Facility', 'Region' ]:
                _model = Place
            elif entity['_type'] in [ 'Organization', 'Company' ]:
                _model = Organisation
            else:
                continue

            try:
                _record = _model.objects.get(uri=entity['__reference'])
            except _model.DoesNotExist, e:
                _record = _model()
            _record.from_calais(entity)
            _record.save()
            model.add_entity(_record)
            records.append(_record)
    except AttributeError:
        # this happens if Calais throws an error. To ensure we continue
        # processing other records pass this error and return False
        return False
    return result, records