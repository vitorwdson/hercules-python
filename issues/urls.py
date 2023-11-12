from django.urls import path

from . import views

app_name = "issues"
urlpatterns = [
    path("issues", views.issue_list.IssueList.as_view(), name="list"),
    path("issues/new", views.new.NewIssue.as_view(), name="new"),
    path("issues/<int:number>", views.issue.issue, name="issue"),
    path(
        "issues/<int:number>/rename",
        views.issue.Rename.as_view(),
        name="rename",
    ),
    path(
        "issues/<int:number>/comment",
        views.issue.comment,
        name="comment",
    ),
]
