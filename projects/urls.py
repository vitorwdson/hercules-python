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
        "select-project",
        views.list.ProjectList.as_view(),
        name="select_project",
    ),
    path(
        "select-project/new",
        views.new.NewProject.as_view(),
        name="new_project",
    ),
]
