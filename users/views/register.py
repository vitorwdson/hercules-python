from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django_htmx.http import HttpResponseClientRedirect

from core.htmx import render_htmx
from core.typing import HttpRequest
from users.forms.new import RegisterForm


class RegisterView(View):
    template_name = "users/register.html"
    redirect_after_register = "core:index"  # TODO: Redirect to profile page

    def get(self, request: HttpRequest):
        form = RegisterForm()

        return render(
            request,
            self.template_name,
            {
                "hide_sidebar": True,
                "form": form,
            },
        )

    def post(self, request: HttpRequest):
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            if request.htmx and not request.htmx.boosted:
                return HttpResponseClientRedirect(
                    reverse(self.redirect_after_register)
                )

            return redirect(self.redirect_after_register)

        return render_htmx(
            request,
            self.template_name,
            {
                "hide_sidebar": True,
                "form": form,
            },
        )
