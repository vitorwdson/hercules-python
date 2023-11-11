from core.htmx import render_htmx
from core.typing import HttpRequest
from users.decorators import login_required, project_required


@login_required
@project_required
def new(request: HttpRequest):
    return render_htmx(
        request,
        "issues/new.html",
    )
