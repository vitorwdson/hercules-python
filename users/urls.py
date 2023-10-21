from django.urls import path

from users import views

app_name = "users"
urlpatterns = [
    path("login", views.login.Login.as_view(), name="login"),
    path("logout", views.login.logout, name="logout"),
    path("register", views.register.RegisterView.as_view(), name="register"),
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
]
