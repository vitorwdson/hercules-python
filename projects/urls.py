from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path(
        "",
        views.index.index,
        name="index",
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
