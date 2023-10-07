from functools import wraps
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http.request import QueryDict
from django.shortcuts import resolve_url

from core.typing import HttpRequest
from core.htmx import redirect_htmx
from projects.user import get_selected_project



def login_required(view_func):
    @wraps(view_func)
    def _wrapper_view(request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        path = request.build_absolute_uri()
        resolved_login_url = resolve_url(settings.LOGIN_URL)

        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if (not login_scheme or login_scheme == current_scheme) and (
            not login_netloc or login_netloc == current_netloc
        ):
            path = request.get_full_path()

        resolved_url = resolve_url(settings.LOGIN_URL)

        login_url_parts = list(urlparse(resolved_url))
        if REDIRECT_FIELD_NAME:
            querystring = QueryDict(login_url_parts[4], mutable=True)
            querystring[REDIRECT_FIELD_NAME] = path  
            login_url_parts[4] = querystring.urlencode(safe="/")

        redirect_url = urlunparse(login_url_parts)
        return redirect_htmx(request, redirect_url)

    return _wrapper_view



def project_required(view_func):
    @wraps(view_func)
    def _wrapper_view(request: HttpRequest, *args, **kwargs):
        get_selected_project(request)

        if request.selected_project is not None:
            return view_func(request, *args, **kwargs)

        return redirect_htmx(request, resolve_url('projects:select_project'))

    return _wrapper_view

