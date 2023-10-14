from django.http import QueryDict
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest
from projects.models import ProjectMember, Role
from projects.user import deselect_project
from users.decorators import login_required, project_required


class Index(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest):
        members = ProjectMember.objects.filter(
            project=request.selected_project.project,
            rejected=False,
            accepted=True,
        ).order_by(
            "role",
            "user__first_name",
            "user__last_name",
            "user__username",
        )

        return render_htmx(
            request,
            "projects/index/page.html",
            {
                "members": members[:3],
            },
        )

    @method_decorator(login_required)
    @method_decorator(project_required)
    def delete(self, request: HttpRequest):
        project = request.selected_project.project

        deleted, message = project.try_delete()
        if deleted:
            deselect_project(request)

            response = show_message(
                None, "success", "Project deleted successfully!"
            )
            response.headers["HX-Redirect"] = reverse("projects:select_project")
            return response

        return show_message(None, "error", message)


class Rename(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest):
        return render_htmx(
            request,
            "projects/index/header.html",
            {
                "renaming": True,
            },
        )

    @method_decorator(login_required)
    @method_decorator(project_required)
    def put(self, request: HttpRequest):
        if request.selected_project.role != Role.OWNER:
            return show_message(
                HttpResponseForbidden(),  # type: ignore
                "error",
                "Only the owner of a project can rename it.",
            )

        data = QueryDict(request.body, True)
        new_name = str(data.get("project-name") or "")
        if not new_name:
            return show_message(
                HttpResponseBadRequest(),  # type: ignore
                "error",
                "The project name can't be empty",
            )

        project = request.selected_project.project
        project.name = new_name
        project.save()

        return render_htmx(request, "projects/index/header.html")
