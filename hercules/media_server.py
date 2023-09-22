import mimetypes
from os import path
from urllib import parse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.views.static import serve


@login_required
def media_server(request: HttpRequest, file_path: str):
    if not file_path:
        raise Http404

    if settings.DEBUG:
        dir_name = settings.MEDIA_ROOT / path.dirname(file_path)
        file_name = path.basename(file_path)

        return serve(request, file_name, dir_name)

    mimetype = mimetypes.guess_type(file_path)[0]
    file_url = settings.SECRET_MEDIA_PATH + file_path

    response = HttpResponse(content_type=mimetype)
    response["X-Accel-Redirect"] = parse.quote(file_url)
    return response
