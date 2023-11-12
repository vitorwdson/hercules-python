from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from projects.models import Project, Team
from users.models import User


class Issue(models.Model):
    class Status(models.IntegerChoices):
        OPEN = 1
        DONE = 2
        CLOSED = 3

    project = models.ForeignKey(Project, on_delete=models.RESTRICT)
    number = models.IntegerField()
    status = models.IntegerField(choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.TextField()

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["project", "number"],
                name="un_project_number",
            ),
        ]


class Counter(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)

    @classmethod
    def get_next(cls, project: Project):
        counter = cls.objects.filter(project=project).first()

        if counter is None:
            counter = cls.objects.create(project=project)

        counter.number += 1

        return counter


class Message(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.RESTRICT)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    body = models.JSONField()


class Assignment(models.Model):
    class Type(models.IntegerChoices):
        USER = 1
        TEAM = 2

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    type = models.IntegerField(choices=Type.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "type", "user", "team"],
                name="un_issue_assignment",
            ),
        ]


class History(models.Model):
    class Type(models.IntegerChoices):
        MESSAGE = 1
        ASSIGNMENT = 2
        STATUS = 3
        TITLE = 4

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(choices=Type.choices)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, blank=True, null=True
    )
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, blank=True, null=True
    )
    status = models.IntegerField(
        choices=Issue.Status.choices, blank=True, null=True
    )
    title = models.TextField(null=True, blank=True)
