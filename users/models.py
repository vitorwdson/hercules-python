import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    def get_picture_path(self, filename):
        name = os.path.basename(filename)

        ext = ""
        if "." in name:
            ext = "." + name.split(".")[-1]

        new_name = uuid.uuid4().hex + ext
        return f"users/{self.pk}/pictures/{new_name}"

    picture = models.ImageField(
        upload_to=get_picture_path, null=True, blank=True
    )
    last_project = models.ForeignKey(
        "projects.Project", on_delete=models.SET_NULL, null=True, blank=True
    )

    def get_name(self):
        full_name = self.get_full_name()

        return full_name.strip() or self.username


class NotificationType(models.IntegerChoices):
    PROJECT_INVITATION = 1
    TEAM_ASSIGNMENT = 2
    ISSUE_ASSIGNMENT = 3
    TEAM_ISSUE_ASSIGNMENT = 4


class Notification(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    notification_type = models.IntegerField(choices=NotificationType.choices)
    project_invitation = models.ForeignKey(
        "projects.ProjectMember",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    team_assignment = models.ForeignKey(
        "projects.TeamMember",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
