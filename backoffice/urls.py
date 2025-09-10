from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users_list, name="users_list"),
]
