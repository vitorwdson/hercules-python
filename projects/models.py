from django.db import models
from django_stubs_ext.db.models import TypedModelMeta


class Role(models.IntegerChoices):
    OWNER = 1
    MANAGER = 2
    DEVELOPER = 3
    TESTER = 4


class Project(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.TextField()


class ProjectMember(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    role = models.IntegerField(choices=Role.choices, default=Role.DEVELOPER)
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)


class Team(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.TextField()


class TeamMember(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_member",
            ),
        ]
