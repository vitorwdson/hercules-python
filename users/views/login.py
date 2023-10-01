from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django_htmx.http import HttpResponseClientRedirect

from core.typing import HttpRequest


class Login(LoginView):
    template_name = 'users/login.html'


def logout(request: HttpRequest):
    auth_logout(request)

    if request.htmx:
        return HttpResponseClientRedirect(settings.LOGIN_URL)
    return redirect(settings.LOGIN_URL)
