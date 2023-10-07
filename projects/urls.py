from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path(
        "select-project",
        views.list.ProjectList.as_view(),
        name="select_project",
    ),
]
