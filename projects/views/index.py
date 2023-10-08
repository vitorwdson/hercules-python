from core.typing import HttpRequest
from core.htmx import render_htmx
from users.decorators import login_required, project_required

@login_required
@project_required
def index(request: HttpRequest):
    return render_htmx(request, 'projects/index.html')
