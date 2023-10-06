from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.typing import HttpRequest

@login_required
def template(request: HttpRequest):
    return render(request, 'base.html')

