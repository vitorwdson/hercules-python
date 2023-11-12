from django.urls import path
from . import views

app_name = 'issues'
urlpatterns = [
    path('issues', views.issue_list.IssueList.as_view(), name='list'),
    path('new', views.new.NewIssue.as_view(), name='new'),
]
