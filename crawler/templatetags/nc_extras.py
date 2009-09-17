from django import template
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

import simplejson

register = template.Library()

@register.filter(name='jsonify')
def jsonify(object):
    """jsonify that object"""
    return mark_safe(simplejson.dumps(object))
jsonify.is_safe = True