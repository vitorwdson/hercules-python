from typing import Any

from django.db.models import Model
from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from core.htmx import redirect_htmx, render_htmx
from core.typing import HttpRequest
from projects.models import Project, ProjectMember, Role
from projects.user import get_selected_project, select_project
from users.decorators import login_required
from users.models import User


class ProjectList(ListView):
    model: type[Model] = Project
    paginate_by = 15
    allow_empty = True
    template_name = "projects/select/list.html"
    request: HttpRequest
    ordering = ["name"]

    def render_to_response(self, context: dict[str, Any], **_: Any):
        return render_htmx(self.request, self.template_name, context)

    @method_decorator(login_required)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        get_selected_project(request)

        return super().get(request, *args, **kwargs)

    @method_decorator(login_required)
    def put(self, request: HttpRequest, *args: Any, **kwargs: Any):
        project_id = request.GET.get("project_id")

        project = get_object_or_404(Project, pk=project_id)
        select_project(request, project)

        return redirect_htmx(request, reverse("projects:index"))

    def get_queryset(self):
        qs = self.model.objects

        user = self.request.user
        if not isinstance(user, User):
            return qs.filter(pk__isnull=True)

        qs = qs.prefetch_related(
            Prefetch(
                "projectmember_set",
                queryset=ProjectMember.objects.filter(
                    user=user, accepted=True, rejected=False
                ),
            )
        ).filter(projectmember__user=user)

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)

        return qs.distinct()
