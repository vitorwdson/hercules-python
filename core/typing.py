from dataclasses import dataclass

from django.http import HttpRequest as BHttpRequest
from django.http import HttpResponse as BHttpResponse
from django_htmx.middleware import HtmxDetails

from projects.models import Project
from users.models import User


@dataclass
class SelectedProject:
    project: Project
    role: int


class HttpRequest(BHttpRequest):
    htmx: HtmxDetails
    user: User
    selected_project: SelectedProject


class HttpResponse(BHttpResponse):
    headers: dict
