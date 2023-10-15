import json
from typing import Any

from django.db.models import Model
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.list import ListView

from core.htmx import render_htmx
from core.typing import HttpRequest, HttpResponse
from projects.forms.team import TeamForm
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        compact = self.request.GET.get("compact")
        if compact in ["true", "True", True]:
            context.update({"compact": True})

        return context

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

        qs = qs.distinct()

        compact = self.request.GET.get("compact")
        if compact in ["true", "True", True]:
            return qs[:3]

        return qs


class NewTeam(View):
    request: HttpRequest
    form = TeamForm
    model = Team

    def get_initial(self):
        return {"project": self.request.selected_project.project.pk}

    @method_decorator(login_required)
    @method_decorator(project_required)
    def get(self, request: HttpRequest):
        form = self.form(
            initial=self.get_initial(),
        )

        response = render_htmx(
            request,
            "projects/teams/dialog.html",
            {
                "form": form,
            },
        )

        response.headers["HX-Trigger"] = json.dumps(
            {"form:showModal": "#new-team-dialog"}
        )

        return response

    @method_decorator(login_required)
    @method_decorator(project_required)
    def post(self, request: HttpRequest):
        form = self.form(
            request.POST,
            initial=self.get_initial(),
        )

        if form.is_valid():
            print(form.cleaned_data)
            form.save()

            response = HttpResponse(b"")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "form:hideModal": "#new-team-dialog",
                    "teams:reloadTable": "",
                },
            )

            return response

        return render_htmx(
            request,
            "projects/teams/dialog.html",
            {
                "form": form,
            },
        )
