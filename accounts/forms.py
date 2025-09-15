from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)

User = get_user_model()


def _add_bootstrap_classes(field, *, is_select=False, is_checkbox=False, is_file=False):
    """
    Tiny helper to consistently apply Bootstrap classes without tears.
    """
    base = field.widget.attrs.get("class", "").split()
    if is_checkbox:
        cls = "form-check-input"
    elif is_select:
        cls = "form-select"
    elif is_file:
        cls = "form-control"
    else:
        cls = "form-control"

    if cls not in base:
        base.append(cls)
    field.widget.attrs["class"] = " ".join(c for c in base if c)


class RegisterForm(UserCreationForm):
    """
    Public registration: username + email + phone.
    Everyone registers as GUEST. No, the public cannot choose 'admin' from a dropdown.
    """

    class Meta:
        model = User
        fields = ("username", "email", "phone")
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Username",
                "autocomplete": "username",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email address",
                "autocomplete": "email",
                "inputmode": "email",
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "Phone number",
                "inputmode": "tel",
                "autocomplete": "tel",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style declared fields
        for name in self.Meta.fields:
            _add_bootstrap_classes(self.fields[name])

        # Style password fields provided by UserCreationForm
        for name in ("password1", "password2"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault(
                    "placeholder",
                    "Password" if name == "password1" else "Confirm password",
                )
                self.fields[name].widget.attrs.setdefault("autocomplete", "new-password")
                _add_bootstrap_classes(self.fields[name])

        # Optional: mute default help texts
        for name in ("password1", "password2"):
            if name in self.fields:
                self.fields[name].help_text = ""

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.GUEST
        if user.email:
            user.email = user.email.strip().lower()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Standard username/password login with Bootstrap-friendly widgets.
    """
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "class": "form-control",
                "placeholder": "Username",
            }
        )
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "form-control",
                "placeholder": "Password",
            }
        )
    )


class ProfileForm(forms.ModelForm):
    """
    Basic profile edit. Users can’t self-escalate here either.
    """
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "avatar"]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "placeholder": "First name",
                "autocomplete": "given-name",
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Last name",
                "autocomplete": "family-name",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email",
                "autocomplete": "email",
                "inputmode": "email",
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "Phone",
                "autocomplete": "tel",
                "inputmode": "tel",
            }),
            "avatar": forms.ClearableFileInput(attrs={
                "accept": "image/*",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "avatar":
                _add_bootstrap_classes(field, is_file=True)
            else:
                _add_bootstrap_classes(field)

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class AdminRoleUpdateForm(forms.Form):
    """
    Admin-side role change with guardrails.
    """
    role = forms.ChoiceField(choices=(), required=True)
    reason = forms.CharField(
        max_length=255,
        required=False,
        help_text="Optional note for audit log.",
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "Reason for change (optional)",
        }),
    )

    def __init__(self, *, target_user, acting_user, **kwargs):
        super().__init__(**kwargs)
        self.target_user = target_user
        self.acting_user = acting_user

        self._actor_can_assign_admin = bool(
            acting_user.is_superuser or getattr(acting_user, "role", "") == User.Roles.ADMIN
        )
        choices = list(User.Roles.choices)

        if target_user.is_superuser:
            choices = [(User.Roles.ADMIN, "Admin")]
        elif not self._actor_can_assign_admin:
            choices = [(v, l) for v, l in choices if v != User.Roles.ADMIN]

        self.fields["role"].choices = choices

        # Bootstrap styling
        _add_bootstrap_classes(self.fields["role"], is_select=True)
        _add_bootstrap_classes(self.fields["reason"])

    def clean(self):
        cleaned = super().clean()
        new_role = cleaned.get("role")

        if not (self.acting_user.is_staff or self.acting_user.role in {User.Roles.ADMIN, User.Roles.STAFF}):
            raise forms.ValidationError("You are not allowed to change roles.")

        if new_role == User.Roles.ADMIN and not self._actor_can_assign_admin:
            raise forms.ValidationError("You are not allowed to assign the Admin role.")

        if self.target_user.is_superuser and new_role != User.Roles.ADMIN:
            raise forms.ValidationError("A superuser must have the Admin role.")

        if self.target_user == self.acting_user and not self.acting_user.is_superuser:
            raise forms.ValidationError("You cannot change your own role.")

        return cleaned


class BootstrapPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "name@example.com",
            "autocomplete": "email",
        })


class BootstrapSetPasswordForm(SetPasswordForm):
    """
    Used by the reset-confirm step so templates can keep using {{ form.as_p }}.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "New password",
            "autocomplete": "new-password",
        })
        self.fields["new_password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm new password",
            "autocomplete": "new-password",
        })
        # Optional: mute help texts
        for name in ("new_password1", "new_password2"):
            if name in self.fields:
                self.fields[name].help_text = ""
