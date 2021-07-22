""" Core context processors. """
from django.conf import settings

def core(request):
    """ Site-wide context processor. """
    site = request.site

    return {
        'enhenced_theme': settings.ENHENCED_THEME,
    }
