from django import forms
from django.contrib.auth.forms import UserChangeForm

from users.models import User


class AlterProfileForm(UserChangeForm):
    password: forms.Field | None = None

    class Meta:
        model = User
