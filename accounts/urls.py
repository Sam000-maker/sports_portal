from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from . import views, views_admin
from .forms import BootstrapPasswordResetForm, BootstrapSetPasswordForm

app_name = "accounts"

urlpatterns = [
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("delete/", views.delete_account_view, name="delete_account"),

    # Password reset
    path("password-reset/",
         auth_views.PasswordResetView.as_view(
             template_name="accounts/password_reset_form.html",
             form_class=BootstrapPasswordResetForm,
             success_url=reverse_lazy("accounts:password_reset_done"),
         ),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(
             template_name="accounts/password_reset_done.html"
         ),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="accounts/password_reset_confirm.html",
             form_class=BootstrapSetPasswordForm,
             success_url=reverse_lazy("accounts:password_reset_complete"),
         ),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(
             template_name="accounts/password_reset_complete.html"
         ),
         name="password_reset_complete"),

    # Admin-facing user management
    path("admin/users/", views_admin.users_list, name="users_list"),
    path("admin/users/<int:user_id>/role/", views_admin.change_user_role, name="change_user_role"),

    # Player requests review
    path("admin/player-requests/", views_admin.player_requests_list, name="player_requests_list"),
    path("admin/player-requests/<int:pk>/<str:action>/", views_admin.review_player_request, name="review_player_request"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
