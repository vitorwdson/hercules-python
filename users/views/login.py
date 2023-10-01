from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django_htmx.http import HttpResponseClientRedirect
from typing import Any

from core.typing import HttpRequest


class Login(LoginView):
    template_name = "users/login.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({'hide_sidebar': True})

        return context


def logout(request: HttpRequest):
    auth_logout(request)

    if request.htmx:
        return HttpResponseClientRedirect(settings.LOGIN_URL)
    return redirect(settings.LOGIN_URL)
