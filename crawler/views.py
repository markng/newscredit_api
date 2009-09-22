from django.http import Http404, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers

def json_object(request, queryset, object_id=None, slug=None,
    slug_field='slug'):
    """docstring for json_object"""
    model = queryset.model
    if object_id:
        queryset = queryset.filter(pk=object_id)
    elif slug and slug_field:
        queryset = queryset.filter(**{slug_field: slug})
    else:
        raise AttributeError, "Generic detail view must be called " \
            "with either an object_id or a slug/slug_field."

    try:
        data = serializers.serialize('json', queryset)
    except ObjectDoesNotExist:
        raise Http404, "No %s found matching the query" %
            (model._meta.verbose_name)

    return HttpResponse(data, mimetype='application/json')