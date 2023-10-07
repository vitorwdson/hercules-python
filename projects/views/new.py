from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from core.htmx import render_htmx
from core.typing import HttpRequest
from projects.forms.project import ProjectForm
from projects.models import Project, ProjectMember, Role


class NewProject(View):
    form = ProjectForm
    model = Project

    def get_initial(self, request: HttpRequest):
        return {}

    @method_decorator(login_required)
    def get(self, request: HttpRequest):
        form = self.form(
            initial=self.get_initial(request),
        )

        return render_htmx(
            request,
            "",
            {
                "form": form,
            },
        )

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
                accepted=True
            )

            request.user.select_project(request, project)

        return render_htmx(
            request,
            "",
            {
                "form": form,
            },
        )
