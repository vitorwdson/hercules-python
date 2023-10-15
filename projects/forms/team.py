from django import forms

from projects.models import Team


class TeamForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    class Meta:
        model = Team
        fields = (
            "name",
            "project",
        )
        widgets = {
            "name": forms.TextInput(attrs={"autofocus": True}),
            "project": forms.HiddenInput(),
        }
