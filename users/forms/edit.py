from typing import Any
from django import forms
from django.contrib.auth.forms import UserChangeForm

from users.models import User


class AlterProfileForm(UserChangeForm):
    password: forms.Field | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields['first_name'].required = True

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]
