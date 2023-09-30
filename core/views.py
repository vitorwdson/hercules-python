from django.shortcuts import render

from core.typing import HttpRequest

def template(request: HttpRequest):
    return render(request, 'base.html')
