from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from core.typing import HttpRequest
from users.decorators import login_required
from users.models import Notification, NotificationType


@login_required
@require_http_methods(["GET"])
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
        response.headers["HX-Trigger"] = "notification:updateList"

    return response


@login_required
@require_http_methods(["GET"])
def notification_list(request: HttpRequest):
    user = request.user
    last_id_str = request.GET.get("last-id")
    first_id_str = request.GET.get("first-id")

    notifications = (
        Notification.objects.select_related(
            "project_invitation__project",
            "project_invitation",
            "team_assignment",
            "team_assignment__team",
        )
        .filter(user=user)
        .order_by("-created_at")
    )

    lazy_load = True
    if last_id_str:
        last_id = None
        try:
            last_id = int(last_id_str)
        except:
            pass

        if last_id is not None:
            notifications = notifications.filter(pk__lt=last_id)
        notifications = notifications[:5]
    elif first_id_str:
        first_id = None
        try:
            first_id = int(first_id_str)
        except:
            pass

        if first_id is not None:
            notifications = notifications.filter(pk__gt=first_id)
            lazy_load = False
        else:
            notifications = notifications.filter(pk=None)
    else:
        notifications = notifications[:5]

    response = render(
        request,
        "users/notification/list.html",
        {
            "notifications": notifications,
            "lazy_load": lazy_load,
        },
    )

    return response


@login_required
@require_http_methods(["PUT"])
def invitation(request: HttpRequest, notification_id: int, accept: bool):
    notification = get_object_or_404(
        Notification.objects.select_related("project_invitation"),
        pk=notification_id,
        user=request.user,
        notification_type=NotificationType.PROJECT_INVITATION,
        project_invitation__accepted=False,
        project_invitation__rejected=False,
    )

    notification.read = True
    if accept:
        notification.project_invitation.accepted = True
        notification.project_invitation.rejected = False
    else:
        notification.project_invitation.accepted = False
        notification.project_invitation.rejected = True

    notification.save()
    notification.project_invitation.save()

    response = render(
        request,
        "users/notification/list-item.html",
        {
            "notification": notification,
            "lazy_load": False,
        },
    )

    return response
