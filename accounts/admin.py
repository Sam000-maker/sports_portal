from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if request and not request.user.is_superuser:
            for f in ("role", "is_superuser", "user_permissions"):
                if f in self.fields:
                    self.fields[f].disabled = True

    def clean_is_superuser(self):
        value = self.cleaned_data.get("is_superuser")
        request = getattr(self, "request", None)
        if request and not request.user.is_superuser:
            return self.instance.is_superuser
        return value


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_superuser", "is_active", "last_login")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "phone", "avatar")}),
        (_("Role"), {"fields": ("role",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "password1", "password2", "email")}),
    )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            ro += ["role", "is_superuser", "user_permissions"]
        ro += ["last_login", "date_joined"]
        return ro

    def get_form(self, request, obj=None, **kwargs):
        defaults = {"form": UserChangeForm}
        defaults.update(kwargs)
        form = super().get_form(request, obj, **defaults)

        class RequestBoundForm(form):  # type: ignore[misc]
            def __new__(cls, *args, **kw):
                kw["request"] = request
                return form(*args, **kw)

        return RequestBoundForm

    def delete_model(self, request, obj):
        if obj.is_superuser and User.objects.filter(is_superuser=True, is_active=True).count() <= 1:
            self.message_user(request, "You can’t delete the last active superuser.", level=messages.ERROR)
            return
        return super().delete_model(request, obj)

    def save_model(self, request, obj, form, change):
        if change and not request.user.is_superuser:
            if "is_superuser" in form.changed_data:
                obj.is_superuser = User.objects.get(pk=obj.pk).is_superuser
            if "role" in form.changed_data:
                obj.role = User.objects.get(pk=obj.pk).role

        if change and "is_superuser" in form.changed_data:
            if not obj.is_superuser and User.objects.filter(is_superuser=True, is_active=True).exclude(pk=obj.pk).count() == 0:
                self.message_user(request, "You can’t demote the last active superuser.", level=messages.ERROR)
                return

        return super().save_model(request, obj, form, change)
