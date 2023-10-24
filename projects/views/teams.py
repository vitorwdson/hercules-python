import json
from typing import Any

from django.db.models import Model, Q, Value
from django.db.models.functions import Concat
from django.http.request import QueryDict
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.list import ListView

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest, HttpResponse
from projects.forms.team import TeamForm
from projects.models import ProjectMember, Team, TeamMember
from users.decorators import login_required, project_required
from users.models import Notification, NotificationType


class Teams(ListView):
    request: HttpRequest
    template_name = "projects/teams/list.html"
    model: type[Model] = Team
    paginate_by = 15
    allow_empty = True
    ordering = ["name"]

    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        compact = self.request.GET.get("compact")
        if compact in ["true", "True", True]:
            context.update({"compact": True})

        return context

    def render_to_response(self, context: dict[str, Any], **_: Any):
        return render_htmx(self.request, self.template_name, context)

    def get_queryset(self):
        qs = self.model.objects

        qs = qs.filter(
            project=self.request.selected_project.project,
        )

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)

        qs = qs.distinct()

        compact = self.request.GET.get("compact")
        if compact in ["true", "True", True]:
            return qs[:3]

        return qs


class NewTeam(View):
    request: HttpRequest
    form = TeamForm
    model = Team

    def get_initial(self):
        return {"project": self.request.selected_project.project.pk}

    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest):
        form = self.form(
            initial=self.get_initial(),
        )

        response = render_htmx(
            request,
            "projects/teams/dialog.html",
            {
                "form": form,
            },
        )

        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#new-team-dialog"}
        )

        return response

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest):
        form = self.form(
            request.POST,
            initial=self.get_initial(),
        )

        if form.is_valid():
            print(form.cleaned_data)
            form.save()

            response = HttpResponse(b"")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#new-team-dialog",
                    "teams:reloadTable": "",
                },
            )

            return response

        return render_htmx(
            request,
            "projects/teams/dialog.html",
            {
                "form": form,
            },
        )


class Members(ListView):
    request: HttpRequest
    team: Team
    template_name = "projects/teams/members/list.html"
    model: type[Model] = TeamMember
    paginate_by = 15
    allow_empty = True
    ordering = [
        "member__user__first_name",
        "member__user__last_name",
        "member__user__username",
    ]

    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(
        self, request: HttpRequest, team_id: int, *args: Any, **kwargs: Any
    ):
        self.team = get_object_or_404(Team, pk=team_id)
        return super().get(request, *args, **kwargs)

    def render_to_response(self, context: dict[str, Any], **_: Any):
        return render_htmx(self.request, self.template_name, context)

    def get_queryset(self):
        qs = self.model.objects

        qs = qs.filter(
            team=self.team,
        )

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)

        return qs.distinct()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update({"team": self.team})

        return context

    @method_decorator(login_required)
    @method_decorator(project_required)
    def delete(self, request: HttpRequest, team_id: int):
        if not request.selected_project.can_create_team:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You are not allowed to delete teams.",
            )

        team = get_object_or_404(Team, pk=team_id)
        deleted, message = team.try_delete()
        if deleted:
            response = show_message(
                None, "success", "Team deleted successfully!"
            )
            response.headers["HX-Redirect"] = reverse("projects:teams")
            return response

        return show_message(None, "error", message)


class Rename(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, team_id: int):
        team = get_object_or_404(Team, pk=team_id)

        return render_htmx(
            request,
            "projects/teams/members/header.html",
            {
                "renaming": True,
                "team": team,
            },
        )

    @method_decorator(login_required)
    @method_decorator(project_required)
    def put(self, request: HttpRequest, team_id: int):
        team = get_object_or_404(Team, pk=team_id)

        if not request.selected_project.can_create_team:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You are not allowed to rename teams.",
            )

        data = QueryDict(request.body, True)
        new_name = str(data.get("team-name") or "")
        if not new_name:
            return show_message(
                HttpResponseBadRequest(),  # type: ignore
                "error",
                "The project name can't be empty",
            )

        team.name = new_name
        team.save()

        return render_htmx(
            request,
            "projects/teams/members/header.html",
            {
                "team": team,
            },
        )


class AssignMember(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, team_id: int):
        team = get_object_or_404(Team, pk=team_id)

        if not request.selected_project.can_create_team:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You must be the project Owner or a Manager to assign members",
            )

        accept = request.headers.get("Accept")
        if accept == "application/json":
            member_ids: list[int] = TeamMember.objects.filter(  # type: ignore
                team=team
            ).values_list("member_id", flat=True)

            filter = request.GET.get("filter") or ""
            members = (
                ProjectMember.objects.annotate(
                    fullname=Concat(
                        "user__first_name", Value(" "), "user__last_name"
                    )
                )
                .select_related("user")
                .exclude(pk__in=member_ids)
                .filter(
                    project=request.selected_project.project,
                    accepted=True,
                    rejected=False,
                )
                .filter(
                    Q(fullname__istartswith=filter)
                    | Q(user__username__istartswith=filter)
                )
            )

            options = [
                {
                    "value": member.pk,
                    "label": member.fullname.strip() or member.user.username,  # type: ignore
                }
                for member in members
            ]

            return JsonResponse(options, safe=False)

        response = render(
            request,
            "projects/teams/members/dialog.html",
            {
                "team": team,
            },
        )
        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#assign-team-member-dialog"}
        )

        return response

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest, team_id: int):
        team = get_object_or_404(Team, pk=team_id)

        if not request.selected_project.can_create_team:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You must be the project Owner or a Manager to assign members",
            )

        member_id = request.POST.get("member")

        member_error = ""
        member = ProjectMember.objects.filter(
            pk=member_id,
            project=request.selected_project.project,
            accepted=True,
            rejected=False,
        ).first()
        if member is None:
            member_error = "Member not found"
        elif member.project != request.selected_project.project:
            member_error = "The selected member is not part of this project"

        team_member = TeamMember.objects.filter(
            team=team,
            member=member,
        ).first()
        if team_member is not None:
            member_error = "The selected member was already part of this team."

        if not member_error and member:
            team_member = TeamMember.objects.create(
                team=team,
                member=member,
            )
            Notification.objects.create(
                user=member.user,
                notification_type=NotificationType.TEAM_ASSIGNMENT,
                team_assignment=team_member,
            )

        response = render(
            request,
            "projects/teams/members/dialog.html",
            {
                "member_error": member_error,
                "team": team,
            },
        )

        if not member_error:
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#assign-team-member-dialog",
                    "form:showMessage": "Member assigned successfully!",
                    "teamMembers:reloadTable": "",
                },
            )

        return response
