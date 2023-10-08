from typing import TypedDict

from core.typing import HttpRequest, SelectedProject
from projects.models import Project, ProjectMember


class SelectedProjectSession(TypedDict):
    project_id: int
    member_id: int
    role: int


def select_project(
    request: HttpRequest, project: Project, member: ProjectMember | None = None
):
    user = request.user
    user.last_project = project
    user.save()

    if member is None:
        member = ProjectMember.objects.get(project=project, user=user)

    request.session["selected_project"] = SelectedProjectSession(
        project_id=project.pk, member_id=member.pk, role=member.role
    )


def get_selected_project(request: HttpRequest):
    selected_project: SelectedProjectSession | None = request.session.get(
        "selected_project"
    )
    if selected_project is None:
        request.selected_project = None  # type: ignore
        return

    project = Project.objects.filter(pk=selected_project["project_id"]).first()
    if project is None:
        request.selected_project = None  # type: ignore
        return

    request.selected_project = SelectedProject(
        project,
        selected_project["role"],
    )


def deselect_project(request: HttpRequest):
    request.session["selected_project"] = None


def select_last_project(request: HttpRequest):
    if request.user.last_project:
        select_project(request, request.user.last_project)
    else:
        deselect_project(request)
