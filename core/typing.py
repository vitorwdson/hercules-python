from django.http import HttpRequest as BHttpRequest, HttpResponse as BHttpResponse

from django_htmx.middleware import HtmxDetails

class HttpRequest(BHttpRequest):
    htmx: HtmxDetails

class HttpResponse(BHttpResponse):
    headers: dict