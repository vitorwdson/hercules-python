from typing import Any

from django.db.models import Model
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.list import ListView

from core.htmx import render_htmx
from core.typing import HttpRequest
from projects.models import Team
from users.decorators import login_required, project_required


class Teams(ListView):
    request: HttpRequest
    template_name = "projects/teams/list.html"
    model: type[Model] = Team
    paginate_by = 15
    allow_empty = True
    ordering = ["name"]

    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        return super().get(request, *args, **kwargs)

    def render_to_response(self, context: dict[str, Any], **_: Any):
        return render_htmx(self.request, self.template_name, context)

    def get_queryset(self):
        qs = self.model.objects

        qs = qs.filter(
            project=self.request.selected_project.project,
        )

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)

        return qs.distinct()


class NewTeam(View):
    pass
