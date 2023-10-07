from django.http import HttpRequest as BHttpRequest, HttpResponse as BHttpResponse

from django_htmx.middleware import HtmxDetails

from users.models import User

class HttpRequest(BHttpRequest):
    htmx: HtmxDetails
    user: User

class HttpResponse(BHttpResponse):
    headers: dict
