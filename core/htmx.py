import json
from typing import Any

from django.http.response import HttpResponse as BHttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django_htmx.http import HttpResponseClientRedirect

from core.typing import HttpRequest, HttpResponse


def render_htmx(
    request: HttpRequest,
    template_name: str,
    context: dict[str, Any] | None = None,
    custom_full_template_name: str | None = None,
    content_type: str | None = None,
    status: int | None = None,
    using: str | None = None,
):
    if context is None:
        context = {}

    if request.htmx and not request.htmx.boosted:
        return render(
            request,
            template_name,
            context,
            content_type,
            status,
            using,
        )

    if custom_full_template_name:
        return render(
            request,
            custom_full_template_name,
            context,
            content_type,
            status,
            using,
        )

    if context is None:
        context = {}

    context["partial_content_template"] = template_name

    return render(
        request,
        "base.html",
        context,
        content_type,
        status,
        using,
    )


def show_message(
    response: HttpResponse | BHttpResponse | None = None,
    icon: str | None = None,
    message: str | None = None,
) -> BHttpResponse:
    if response is None:
        response = HttpResponse(b"")

    if icon is None and message is None:
        response.headers["HX-Trigger"] = "form:showMessage"
    else:
        response.headers["HX-Trigger"] = json.dumps(
            {
                "form:showMessage": {
                    "icon": icon,
                    "message": message,
                }
            }
        )

    return response


def redirect_htmx(request: HttpRequest, url: str) -> BHttpResponse:
    if request.htmx and not request.htmx.boosted:
        return HttpResponseClientRedirect(url)
    else:
        return HttpResponseRedirect(url)
