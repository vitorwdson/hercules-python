from typing import Any

from django.contrib.auth.decorators import login_required
from django.db.models import Model
from django.db.models.query import Prefetch
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from core.htmx import render_htmx
from core.typing import HttpRequest
from projects.models import Project, ProjectMember, Role
from users.models import User


class ProjectList(ListView):
    model: type[Model] = Project
    paginate_by = 15
    allow_empty = True
    template_name = "projects/list.html"
    request: HttpRequest
    ordering = ['name']

    def render_to_response(self, context: dict[str, Any], **_: Any):
        return render_htmx(self.request, self.template_name, context)

    @method_decorator(login_required)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = self.model.objects

        user = self.request.user
        if not isinstance(user, User):
            return qs.filter(pk__isnull=True)

        qs = qs.prefetch_related(
            Prefetch('projectmember_set', queryset=ProjectMember.objects.filter(user=user))
        ).filter(projectmember__user=user)

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            qs = qs.order_by(*ordering)

        return  qs.distinct()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        data = super().get_context_data(**kwargs)

        for obj in data['object_list']:
            obj.can_edit = False

            member: ProjectMember | None = obj.projectmember_set.first()
            if member is None:
                continue

            if member.role in [Role.OWNER, Role.MANAGER]:
                obj.can_edit = True

        return data
