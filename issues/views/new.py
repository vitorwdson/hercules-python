import json

from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django_htmx.http import HttpResponseClientRedirect

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest
from issues.models import Counter, History, Issue, Message
from users.decorators import login_required, project_required


class NewIssue(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest):
        return render_htmx(
            request,
            "issues/new.html",
        )

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest):
        if not request.selected_project.can_create_issue:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You are not allowed to create issues in this project.",
            )

        title = request.POST.get("title")
        description_json = request.POST.get("description")

        if not title:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "The issue title is required.",
            )

        try:
            assert description_json is not None
            description: dict = json.loads(description_json)
        except:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "The issue description is required.",
            )

        counter = Counter.get_next(request.selected_project.project)
        try:
            issue = Issue.objects.create(
                project=request.selected_project.project,
                number=counter.number,
                created_by=request.user,
                title=title,
            )
            message = Message.objects.create(
                issue=issue,
                created_by=request.user,
                body=description,
            )
            History.objects.create(
                issue=issue,
                user=request.user,
                type=History.Type.MESSAGE,
                message=message,
            )
        except:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "Server error",
            )

        counter.save()

        return HttpResponseClientRedirect(reverse("issues:list"))  # TODO
