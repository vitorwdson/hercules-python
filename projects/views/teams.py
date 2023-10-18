import json
from typing import Any

from django.db.models import Model
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.list import ListView

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest, HttpResponse
from projects.forms.team import TeamForm
from projects.models import Team, TeamMember
from users.decorators import login_required, project_required


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
    def get(self, request: HttpRequest):
        if not request.selected_project.can_invite:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You must be the project Owner or a Manager to invite members",
            )

        accept = request.headers.get("Accept")
        if accept == "application/json":
            member_ids: list[int] = ProjectMember.objects.filter(  # type: ignore
                project=request.selected_project.project,
                rejected=False,
            ).values_list(
                "user_id", flat=True
            )

            filter = request.GET.get("filter") or ""
            users = (
                User.objects.annotate(
                    fullname=Concat("first_name", Value(" "), "last_name")
                )
                .exclude(pk__in=member_ids)
                .filter(
                    Q(fullname__istartswith=filter)
                    | Q(username__istartswith=filter)
                )
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
            "projects/members/dialog.html",
            {"roles": Role.choices[1:]},
        )
        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#invite-member-dialog"}
        )

        return response

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest):
        if not request.selected_project.can_invite:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "You must be the project Owner or a Manager to invite members",
            )

        user_id = request.POST.get("user")
        role_str = request.POST.get("role")

        user_error = ""
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            user_error = "User not found"

        member = ProjectMember.objects.filter(
            project=request.selected_project.project,
            user=user,
        ).first()
        if member is not None:
            if member.accepted:
                user_error = "The selected user is already a member"
            elif not member.rejected:
                user_error = "The selected user was already invited"

        role_error = ""
        role: int | None = None
        try:
            role = int(role_str or "")
        except:
            role_error = "No role selected"

        if role not in Role.values:
            role_error = "Invalid role"

        if not user_error and not role_error:
            if member is not None:
                member.delete()

            ProjectMember.objects.create(
                project=request.selected_project.project,
                user=user,
                role=role,
            )

        response = render(
            request,
            "projects/members/dialog.html",
            {
                "user_error": user_error,
                "role_error": role_error,
                "roles": Role.choices[1:],
            },
        )

        if not user_error and not role_error:
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#invite-member-dialog",
                    "form:showMessage": "Member invited successfully!",
                },
            )

        return response
