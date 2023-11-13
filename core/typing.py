from dataclasses import dataclass

from django.http import HttpRequest as BHttpRequest
from django.http import HttpResponse as BHttpResponse
from django.utils.functional import cached_property
from django_htmx.middleware import HtmxDetails

from projects.models import Project, Role
from users.models import User


@dataclass
class SelectedProject:
    project: Project
    role: int

    @cached_property
    def is_owner(self):
        return self.role == Role.OWNER

    @cached_property
    def can_invite(self):
        return self.role in [Role.OWNER, Role.MANAGER]

    @cached_property
    def can_create_team(self):
        return self.role in [Role.OWNER, Role.MANAGER]

    @cached_property
    def can_create_issue(self):
        return True  # TODO

    @cached_property
    def can_rename_issues(self):
        return self.role in [Role.OWNER, Role.MANAGER]

    @cached_property
    def can_change_issue_status(self):
        return self.role in [Role.OWNER, Role.MANAGER]

    @cached_property
    def can_assign_to_issue(self):
        return self.role in [Role.OWNER, Role.MANAGER]


class HttpRequest(BHttpRequest):
    htmx: HtmxDetails
    user: User
    selected_project: SelectedProject


class HttpResponse(BHttpResponse):
    headers: dict
