from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest
from projects.user import deselect_project
from users.decorators import login_required, project_required


class Index(View):
    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest):
        return render_htmx(request, "projects/index/page.html")

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
