import json

from django.http.request import QueryDict
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRefresh

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest, HttpResponse
from issues.models import Assignment, History, Issue, Message
from users.decorators import login_required, project_required


@login_required
@project_required
def issue(request: HttpRequest, number: int):
    issue = get_object_or_404(
        Issue, project=request.selected_project.project, number=number
    )
    history = (
        History.objects.filter(issue=issue)
        .select_related(
            "assignment__user",
            "assignment__team",
            "message",
            "user",
        )
        .order_by("created_at")
    )
    assignments = (
        Assignment.objects.select_related("user", "team")
        .filter(issue=issue)
        .order_by(
            "user__first_name",
            "user__last_name",
            "user__username",
            "team__name",
        )
    )

    user_assignments = [
        a for a in assignments if a.type == Assignment.Type.USER
    ]
    team_assignments = [
        a for a in assignments if a.type == Assignment.Type.TEAM
    ]

    return render_htmx(
        request,
        "issues/issue.html",
        {
            "issue": issue,
            "history": history,
            "HistoryType": History.Type,
            "user_assignments": user_assignments,
            "team_assignments": team_assignments,
        },
    )


class Rename(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, number: int):
        issue = get_object_or_404(
            Issue, project=request.selected_project.project, number=number
        )

        can_rename = issue.created_by_id == request.user.pk  # type: ignore
        can_rename = can_rename or request.selected_project.can_rename_issues
        if not can_rename:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "Only the owner of a project can rename it.",
            )

        return render(
            request,
            "issues/issue.html",
            {
                "renaming": True,
                "issue": issue,
            },
        )

    @method_decorator(login_required)
    @method_decorator(project_required)
    def put(self, request: HttpRequest, number: int):
        issue = get_object_or_404(
            Issue, project=request.selected_project.project, number=number
        )

        can_rename = issue.created_by_id == request.user.pk  # type: ignore
        can_rename = can_rename or request.selected_project.can_rename_issues
        if not can_rename:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "Only the owner of a project can rename it.",
            )

        data = QueryDict(request.body, True)
        new_title = str(data.get("issue-title") or "")
        if not new_title:
            return show_message(
                HttpResponseBadRequest(),  # type: ignore
                "error",
                "The issue title can't be empty",
            )

        history = None
        if issue.title != new_title:
            issue.title = new_title
            issue.save()

            history = History.objects.create(
                issue=issue,
                user=request.user,
                type=History.Type.TITLE,
                title=new_title,
            )

        html = render_to_string(
            request=request,
            template_name="issues/issue.html",
            context={"issue": issue},
        )

        if history is not None:
            html += render_to_string(
                request=request,
                template_name="issues/change.html",
                context={
                    "HistoryType": History.Type,
                    "issue": issue,
                    "change": history,
                    "oob": True,
                },
            )

        return HttpResponse(html)


@login_required
@project_required
@require_POST
def comment(request: HttpRequest, number: int):
    issue = get_object_or_404(
        Issue, project=request.selected_project.project, number=number
    )
    comment_json = request.POST.get("comment")
    status_str = request.POST.get("status")

    try:
        status = int(status_str or '')
    except:
        status = None

    can_change_status = issue.created_by_id == request.user.pk  # type: ignore
    can_change_status = can_change_status or request.selected_project.can_change_issue_status
    if status is not None and not can_change_status:
        return show_message(
            HttpResponseForbidden(),  # type: ignore
            "error",
            "Only the owner of a project can rename it.",
        )

    try:
        assert comment_json is not None
        comment: dict = json.loads(comment_json)
    except:
        return show_message(
            HttpResponseForbidden(),  # type: ignore
            "error",
            "The comment body is required.",
        )

    try:
        message = Message.objects.create(
            issue=issue,
            created_by=request.user,
            body=comment,
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

    if status is not None and can_change_status:
        issue.status = status
        issue.save()

        History.objects.create(
            issue=issue,
            user=request.user,
            type=History.Type.STATUS,
            status=status,
        )

    return HttpResponseClientRefresh()
