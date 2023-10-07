import json
from django.urls import reverse

from django.utils.decorators import method_decorator
from django.views import View

from core.htmx import render_htmx
from core.typing import HttpRequest, HttpResponse
from projects.forms.project import ProjectForm
from projects.models import Project, ProjectMember, Role
from projects.user import select_project
from users.decorators import login_required


class NewProject(View):
    form = ProjectForm
    model = Project

    def get_initial(self, _: HttpRequest):
        return {}

    @method_decorator(login_required)
    def get(self, request: HttpRequest):
        form = self.form(
            initial=self.get_initial(request),
        )

        response = render_htmx(
            request,
            "projects/new.html",
            {
                "form": form,
            },
        )

        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#new-project-dialog"}
        )

        return response

    @method_decorator(login_required)
    def post(self, request: HttpRequest):
        form = self.form(
            request.POST,
            initial=self.get_initial(request),
        )

        if form.is_valid():
            project = form.save()
            ProjectMember.objects.create(
                project=project,
                user=request.user,
                role=Role.OWNER,
                accepted=True,
            )

            select_project(request, project)

            response = HttpResponse(b"")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#new-project-dialog",
                },
            )
            response.headers["HX-Location"] = reverse('core:index')

            return response

        return render_htmx(
            request,
            "projects/new.html",
            {
                "form": form,
            },
        )

