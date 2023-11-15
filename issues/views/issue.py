import json

from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http.request import QueryDict
from django.http.response import (HttpResponseBadRequest,
                                  HttpResponseForbidden, JsonResponse)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRefresh

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest, HttpResponse
from issues.models import Assignment, History, Issue, Message
from projects.models import ProjectMember, Team, TeamMember
from users.decorators import login_required, project_required
from users.models import Notification, NotificationType, User


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
                _("Only the owner of a project can rename it."),
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
                _("Only the owner of a project can rename it."),
            )

        data = QueryDict(request.body, True)
        new_title = str(data.get("issue-title") or "")
        if not new_title:
            return show_message(
                HttpResponseBadRequest(),  # type: ignore
                "error",
                _("The issue title can't be empty"),
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
        status = int(status_str or "")
    except:
        status = None

    can_change_status = issue.created_by_id == request.user.pk  # type: ignore
    can_change_status = (
        can_change_status or request.selected_project.can_change_issue_status
    )
    if status is not None and not can_change_status:
        return show_message(
            HttpResponseForbidden(),  # type: ignore
            "error",
            _("Only the owner of a project can rename it."),
        )

    try:
        assert comment_json is not None
        comment: dict = json.loads(comment_json)
    except:
        return show_message(
            HttpResponseForbidden(),  # type: ignore
            "error",
            _("The comment body is required."),
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
            _("Server error"),
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


class AssignUser(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, number: int):
        issue = get_object_or_404(
            Issue, project=request.selected_project.project, number=number
        )

        can_assign_user = issue.created_by_id == request.user.pk  # type: ignore
        can_assign_user = (
            can_assign_user or request.selected_project.can_assign_to_issue
        )
        if not can_assign_user:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                _("You can not assign users to this issue."),
            )

        accept = request.headers.get("Accept")
        if accept == "application/json":
            assigned_ids: list[int] = Assignment.objects.filter(  # type: ignore
                issue=issue,
                type=Assignment.Type.USER,
            ).values_list("user_id", flat=True)

            member_ids = ProjectMember.objects.filter(
                project=request.selected_project.project,
                accepted=True,
                rejected=False,
            ).values_list("user_id", flat=True)

            filter = request.GET.get("filter") or ""
            users = (
                User.objects.annotate(
                    fullname=Concat("first_name", Value(" "), "last_name")
                )
                .exclude(pk__in=assigned_ids)
                .filter(
                    Q(fullname__istartswith=filter)
                    | Q(username__istartswith=filter)
                )
                .filter(pk__in=member_ids)
            )

            options = [
                {
                    "value": user.pk,
                    "label": user.fullname.strip() or user.username,  # type: ignore
                }
                for user in users
            ]

            return JsonResponse(options, safe=False)

        response = render(
            request,
            "issues/assign-user.html",
            {"issue": issue},
        )
        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#assign-user-dialog"}
        )

        return response

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest, number: int):
        issue = get_object_or_404(
            Issue, project=request.selected_project.project, number=number
        )

        can_assign_user = issue.created_by_id == request.user.pk  # type: ignore
        can_assign_user = (
            can_assign_user or request.selected_project.can_assign_to_issue
        )
        if not can_assign_user:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                _("You can not assign users to this issue."),
            )

        user_id = request.POST.get("user")

        user_error = ""
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            user_error = _("User not found")

        member = Assignment.objects.filter(
            issue=issue,
            type=Assignment.Type.USER,
            user=user,
        ).first()
        if member is not None:
            user_error = _("The selected user is already assigned")

        if not user_error and user is not None:
            assignment = Assignment.objects.create(
                issue=issue,
                type=Assignment.Type.USER,
                user=user,
            )
            Notification.objects.create(
                user=user,
                notification_type=NotificationType.ISSUE_ASSIGNMENT,
                issue_assignment=assignment,
            )

            picture_url = ""
            if user.picture:
                picture_url = user.picture.url
            else:
                picture_url = static("img/profile-placeholder.png")

            response = HttpResponse(
                f"""
                    <div hx-swap-oob="beforebegin:#assign-user-btn-container">
                        <div class="flex flex-row items-center justify-start gap-2">
                            <img
                              class="object-contain w-8 h-8 rounded-full overflow-hidden"
                              src="{picture_url}"
                              alt="{_('Profile picture')}"
                            />
                            <p>{user.get_name()}</p>
                        </div>
                    </div>
                    <p hx-swap-oob="delete:#no-users-assigned-p"></p>
                """
            )
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#assign-user-dialog",
                    "form:showMessage": _("User assigned successfully!"),
                },
            )
            return response

        return render(
            request,
            "issues/assign-user.html",
            {
                "issue": issue,
                "user_error": user_error,
            },
        )


class AssignTeam(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, number: int):
        issue = get_object_or_404(
            Issue, project=request.selected_project.project, number=number
        )

        can_assign_team = issue.created_by_id == request.user.pk  # type: ignore
        can_assign_team = (
            can_assign_team or request.selected_project.can_assign_to_issue
        )
        if not can_assign_team:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                _("You can not assign teams to this issue."),
            )

        accept = request.headers.get("Accept")
        if accept == "application/json":
            assigned_ids: list[int] = Assignment.objects.filter(  # type: ignore
                issue=issue,
                type=Assignment.Type.TEAM,
            ).values_list("team_id", flat=True)

            filter = request.GET.get("filter") or ""
            teams = Team.objects.exclude(pk__in=assigned_ids).filter(
                name__istartswith=filter
            )

            options = [
                {
                    "value": team.pk,
                    "label": team.name,
                }
                for team in teams
            ]

            return JsonResponse(options, safe=False)

        response = render(
            request,
            "issues/assign-team.html",
            {"issue": issue},
        )
        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#assign-team-dialog"}
        )

        return response

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest, number: int):
        issue = get_object_or_404(
            Issue, project=request.selected_project.project, number=number
        )

        can_assign_team = issue.created_by_id == request.user.pk  # type: ignore
        can_assign_team = (
            can_assign_team or request.selected_project.can_assign_to_issue
        )
        if not can_assign_team:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                _("You can not assign teams to this issue."),
            )

        team_id = request.POST.get("team")

        team_error = ""
        team = Team.objects.filter(pk=team_id).first()
        if team is None:
            team_error = _("Team not found")

        team_members = TeamMember.objects.filter(team=team).select_related(
            "member__user"
        )

        member = Assignment.objects.filter(
            issue=issue,
            type=Assignment.Type.TEAM,
            team=team,
        ).first()
        if member is not None:
            team_error = _("The selected team is already assigned")

        if not team_error and team is not None:
            assignment = Assignment.objects.create(
                issue=issue,
                type=Assignment.Type.TEAM,
                team=team,
            )

            for t_member in team_members:
                Notification.objects.create(
                    user=t_member.member.user,
                    notification_type=NotificationType.ISSUE_ASSIGNMENT,
                    issue_assignment=assignment,
                )

            response = HttpResponse(
                f"""
                    <div hx-swap-oob="beforebegin:#assign-team-btn-container">
                        <div class="flex flex-row items-center justify-start mt-1">
                            <p>{team.name}</p>
                        </div>
                    </div>
                    <p hx-swap-oob="delete:#no-teams-assigned-p"></p>
                """
            )
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#assign-team-dialog",
                    "form:showMessage": _("Team assigned successfully!"),
                },
            )
            return response

        return render(
            request,
            "issues/assign-team.html",
            {
                "issue": issue,
                "team_error": team_error,
            },
        )
