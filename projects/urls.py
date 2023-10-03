from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path("", views.projects.ProjectList.as_view(), name="list"),
]
