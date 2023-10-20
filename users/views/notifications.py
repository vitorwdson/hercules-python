from django.shortcuts import render

from core.typing import HttpRequest
from users.decorators import login_required
from users.models import Notification


@login_required
def counter(request: HttpRequest):
    user = request.user

    previous_count = int(request.GET.get("previous-count") or "0")
    count = Notification.objects.filter(user=user, read=False).count()
    update_list = count > previous_count

    if count == 0:
        count_str = ""
    elif count < 10:
        count_str = str(count)
    else:
        count_str = "9+"

    response = render(
        request,
        "users/notification/counter.html",
        {
            "count": count,
            "count_str": count_str,
            "update_list": update_list,
            "delay": True,
        },
    )

    if update_list:
        response.headers['HX-Trigger'] = "notification:getNewList"

    return response
