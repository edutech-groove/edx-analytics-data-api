import logging

from django.conf import settings
from django.db import connections
from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions, schemas
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.views import APIView
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

logger = logging.getLogger(__name__)


def handle_internal_server_error(_request):
    """Notify the client that an error occurred processing the request without providing any detail."""
    return _handle_error(500)


def handle_missing_resource_error(_request, exception=None):  # pylint: disable=unused-argument
    """Notify the client that the requested resource could not be found."""
    return _handle_error(404)


def _handle_error(status_code):
    info = {
        'status': status_code
    }

    renderer = JSONRenderer()
    content_type = '{media}; charset={charset}'.format(media=renderer.media_type, charset=renderer.charset)
    return HttpResponse(renderer.render(info), content_type=content_type, status=status_code)


class SwaggerSchemaView(APIView):
    """
    Renders the swagger schema for the documentation regardless of permissions.
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [
        OpenAPIRenderer,
        SwaggerUIRenderer
    ]

    def get(self, _request):
        generator = schemas.SchemaGenerator(title='Analytics API')
        return Response(generator.get_schema())

    @staticmethod
    def my_exception_handler(exc, context):
        response = exception_handler(exc, context)
        if response.status_code >= 400:
            context['enhenced_theme'] = settings.ENHENCED_THEME if hasattr(settings, 'ENHENCED_THEME') else {}
            return HttpResponse(loader.get_template('403.html').render(context), content_type='text/html', status=403)
        return response

    def get_exception_handler(self):
        return self.my_exception_handler


class StatusView(APIView):
    """
    Simple check to determine if the server is alive

    Return no data, a simple 200 OK status code is sufficient to indicate that the server is alive. This endpoint is
    public and does not require an authentication token to access it.

    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        return Response({})


class AuthenticationTestView(APIView):
    """
    Verifies that the client is authenticated

    Returns HTTP 200 if client is authenticated, HTTP 401 if not authenticated

    """

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        return Response({})


class HealthView(APIView):
    """
   A more comprehensive check to see if the system is fully operational.

   This endpoint is public and does not require an authentication token to access it.

   The returned structure contains the following fields:

   - overall_status: Can be either "OK" or "UNAVAILABLE".
   - detailed_status: More detailed information about the status of the system.
       - database_connection: Status of the database connection. Can be either "OK" or "UNAVAILABLE".

   """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        OK = 'OK'
        UNAVAILABLE = 'UNAVAILABLE'

        overall_status = UNAVAILABLE
        db_conn_status = UNAVAILABLE

        try:
            connection_name = getattr(settings, 'ANALYTICS_DATABASE', 'default')
            cursor = connections[connection_name].cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()

                overall_status = OK
                db_conn_status = OK
            finally:
                cursor.close()
        except Exception:  # pylint: disable=broad-except
            pass

        response = {
            "overall_status": overall_status,
            "detailed_status": {
                'database_connection': db_conn_status
            }
        }

        if overall_status == UNAVAILABLE:
            logger.error("Health check failed: %s", response)

        return Response(response, status=200 if overall_status == OK else 503)
