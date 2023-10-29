from django.utils.decorators import method_decorator
from django.views import View

from core.htmx import render_htmx
from core.typing import HttpRequest
from users.decorators import login_required


class Profile(View):
    @method_decorator(login_required)
    def get(self, request: HttpRequest):
        print(request.htmx, bool(request.htmx))
        return render_htmx(request, "users/profile/profile.html")
