"""
Template tags and helper functions for escaping script tag.
"""
import json
import re

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
register = template.Library()

@register.filter
def escape_json(data):
    """
    Escape a JSON string (or convert a dict to a JSON string, and then
    escape it) for being embedded within an HTML template.
    """
    json_string = json.dumps(data) if isinstance(data, dict) else data
    json_string = json_string.replace("&", "\\u0026")
    json_string = json_string.replace(">", "\\u003e")
    json_string = json_string.replace("<", "\\u003c")
    return mark_safe(json_string)

@register.filter
def fec_url(url):
    """
    get url from input then adding /static as prefix and _v=$$$ as suffix
    """
    if hasattr(settings, 'FEC_VERSION') and settings.FEC_VERSION is not None:
        fec_version = re.sub('[a-zA-Z.]', '', settings.FEC_VERSION)
        return "/static/fec/{}/{}?_v={}".format(settings.FEC_CLIENT, url, fec_version)
    return url