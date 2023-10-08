from django.shortcuts import render
from core.typing import HttpRequest
from users.decorators import login_required, project_required

@login_required
@project_required
def index(request: HttpRequest):
    return render(request, 'base.html')
