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
