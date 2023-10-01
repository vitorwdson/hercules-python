from typing import Any

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django_htmx.http import HttpResponseClientRedirect

from core.typing import HttpRequest


class Login(LoginView):
    template_name = "users/login.html"
    request: HttpRequest

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"hide_sidebar": True})

        return context

    def form_valid(self, _):
        redirect_url = self.get_success_url()

        if self.request.htmx and not self.request.htmx.boosted:
            return HttpResponseClientRedirect(redirect_url)

        return redirect(redirect_url)


def logout(request: HttpRequest):
    auth_logout(request)

    if request.htmx and not request.htmx.boosted:
        return HttpResponseClientRedirect(settings.LOGIN_URL)
    return redirect(settings.LOGIN_URL)
