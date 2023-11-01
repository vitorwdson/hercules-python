from django.urls import path

from users import views

app_name = "users"
urlpatterns = [
    path("login", views.login.Login.as_view(), name="login"),
    path("logout", views.login.logout, name="logout"),
    path("register", views.register.RegisterView.as_view(), name="register"),
    path("profile", views.profile.profile, name="profile"),
    path(
        "profile/picture",
        views.profile.upload_picture,
        name="upload_picture",
    ),
    path(
        "notifications/counter",
        views.notifications.counter,
        name="notifications_counter",
    ),
    path(
        "notifications/list",
        views.notifications.notification_list,
        name="notifications_list",
    ),
    path(
        "notifications/invitation/<int:notification_id>/accept",
        views.notifications.invitation,
        kwargs={"accept": True},
        name="notifications_accept_invitation",
    ),
    path(
        "notifications/invitation/<int:notification_id>/reject",
        views.notifications.invitation,
        kwargs={"accept": False},
        name="notifications_reject_invitation",
    ),
]
