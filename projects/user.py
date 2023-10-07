from core.typing import HttpRequest
from projects.models import Project


def select_project(request: HttpRequest, project: Project):
    user = request.user
    user.last_project = project
    user.save()

    request.session["selected_project_id"] = project.pk


def get_selected_project(request: HttpRequest) -> Project | None:
    project_id = request.session.get("selected_project_id")
    if project_id is None:
        return None

    return Project.objects.filter(pk=project_id).first()


def select_last_project(request: HttpRequest):
    if request.user.last_project:
        request.session["selected_project_id"] = request.user.last_project.pk
    else:
        request.session["selected_project_id"] = None


def get_last_selected_project(request: HttpRequest) -> Project | None:
    select_last_project(request)
    return get_selected_project(request)
