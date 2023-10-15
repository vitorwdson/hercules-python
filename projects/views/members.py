import json
from typing import Any

from django.db.models import Model, Q
from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.http.response import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.list import ListView

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest
from projects.models import ProjectMember, Role
from users.decorators import login_required, project_required
from users.models import User


class Members(ListView):
    request: HttpRequest
    template_name = "projects/members/list.html"
    model: type[Model] = ProjectMember
    paginate_by = 15
    allow_empty = True
    ordering = ["role", "user__first_name", "user__last_name", "user__username"]

    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        return super().get(request, *args, **kwargs)

    def render_to_response(self, context: dict[str, Any], **_: Any):
        return render_htmx(self.request, self.template_name, context)

    def get_queryset(self):
        qs = self.model.objects

        qs = qs.filter(
            project=self.request.selected_project.project,
            rejected=False,
            accepted=True,
        )

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)

        return qs.distinct()


class InviteMember(View):
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
        response.headers["HX-Trigger"] = json.dumps(
            {
                "form:hideModal": "#invite-member-dialog",
                "form:showMessage": "Member invited successfully!",
            },
        )

        return response
