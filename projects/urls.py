from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path(
        "",
        views.index.Index.as_view(),
        name="index",
    ),
    path(
        "rename",
        views.index.Rename.as_view(),
        name="rename",
    ),
    path(
        "members/invite",
        views.members.InviteMember.as_view(),
        name="invite_member",
    ),
    path(
        "select-project",
        views.select.ProjectList.as_view(),
        name="select_project",
    ),
    path(
        "select-project/new",
        views.new.NewProject.as_view(),
        name="new_project",
    ),
]
