from django.http.response import HttpResponseBadRequest
from django.views import View
from django.views.decorators.http import require_POST, require_safe
from PIL import Image

from core.htmx import render_htmx, show_message
from core.typing import HttpRequest
from users.decorators import login_required
from users.forms.picture import PictureForm


@login_required
@require_safe
def profile(request: HttpRequest):
    return render_htmx(request, "users/profile/profile.html")


@login_required
@require_POST
def upload_picture(request: HttpRequest):
    form = PictureForm(request.POST, request.FILES)
    if not form.is_valid():
        print(request.FILES)
        print(form.cleaned_data)
        return show_message(
            HttpResponseBadRequest(),  # type: ignore
            "error",
            "The uploaded file is not a valid image.",
        )

    picture = form.cleaned_data["picture"]

    request.user.picture = picture
    request.user.save()

    image = Image.open(request.user.picture.path)

    width, height = image.size
    size = min(image.size)
    xoffset = int((width - size) / 2)
    yoffset = int((height - size) / 2)

    image = image.crop(
        (
            xoffset,
            yoffset,
            xoffset + size,
            yoffset + size,
        )
    )

    image.save(request.user.picture.path)

    return render_htmx(request, "users/profile/picture-img.html", {"oob": True})
