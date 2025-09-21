#accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)

from .models import Sport, PendingPlayerRequest

User = get_user_model()


def _add_bootstrap_classes(field, *, is_select=False, is_checkbox=False, is_file=False):
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
        for name in self.Meta.fields:
            _add_bootstrap_classes(self.fields[name])
        for name in ("password1", "password2"):
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault(
                    "placeholder",
                    "Password" if name == "password1" else "Confirm password",
                )
                self.fields[name].widget.attrs.setdefault("autocomplete", "new-password")
                _add_bootstrap_classes(self.fields[name])
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
    Single dropdown for sport on the profile page.
    We keep the M2M on the model but only let them pick one here.
    """
    sport_code = forms.ChoiceField(
        required=False,
        choices=[("", "— Select a sport —")] + list(Sport.Code.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Sport",
    )

    class Meta:
        model = User
        # no direct "sports" in fields; we manage it via sport_code
        fields = ["first_name", "last_name", "email", "phone", "avatar"]

        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name", "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "email", "inputmode": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone", "autocomplete": "tel", "inputmode": "tel"}),
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Styling
        for name, field in self.fields.items():
            if name == "avatar":
                _add_bootstrap_classes(field, is_file=True)
            elif name == "sport_code":
                _add_bootstrap_classes(field, is_select=True)
            else:
                _add_bootstrap_classes(field)

        # Preselect one current sport if user already has any
        if self.instance and self.instance.pk:
            first_code = (
                self.instance.sports.values_list("code", flat=True).order_by("code").first()
            )
            if first_code:
                self.fields["sport_code"].initial = first_code

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Map the single code to the M2M (store one sport)
        code = self.cleaned_data.get("sport_code") or ""
        if code:
            sport_obj, _ = Sport.objects.get_or_create(code=code)
            if commit:
                if not user.pk:
                    user.save()
                user.sports.set([sport_obj])
            else:
                self._sport_to_set = [sport_obj]
        else:
            # No selection clears sports
            if commit:
                user.sports.clear()
            else:
                self._sport_to_set = []

        return user


class PendingPlayerRequestForm(forms.ModelForm):
    """
    Replace the M2M widget with a single dropdown named 'sport'.
    We'll set the M2M manually in save().
    """
    sport = forms.ModelChoiceField(
        queryset=Sport.objects.all().order_by("code"),
        required=True,
        empty_label="— Select a sport —",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Sport",
    )

    class Meta:
        model = PendingPlayerRequest
        # We intentionally exclude "sports" and handle it manually
        fields = ["bio", "achievements"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _add_bootstrap_classes(self.fields["sport"], is_select=True)
        _add_bootstrap_classes(self.fields["bio"])
        _add_bootstrap_classes(self.fields["achievements"])

    def clean(self):
        cleaned = super().clean()

        if not self.user or not self.user.is_authenticated:
            raise forms.ValidationError("Login required.")

        # Name requirement: both first and last name must be present
        missing_first = not (self.user.first_name or "").strip()
        missing_last = not (self.user.last_name or "").strip()
        if missing_first or missing_last:
            raise forms.ValidationError(
                "Please add your First and Last name in your profile before requesting to become a player."
            )

        if self.user.player_requests.filter(status=PendingPlayerRequest.Status.PENDING).exists():
            raise forms.ValidationError("You already have a pending request.")

        if not cleaned.get("sport"):
            raise forms.ValidationError("Select a sport.")

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.user = self.user
        if commit:
            obj.save()
            # set exactly one sport in the M2M
            obj.sports.set([self.cleaned_data["sport"]])
        else:
            self._sport_to_set = [self.cleaned_data["sport"]]
        return obj


class AdminRoleUpdateForm(forms.Form):
    role = forms.ChoiceField(choices=(), required=True)
    reason = forms.CharField(
        max_length=255,
        required=False,
        help_text="Optional note for audit log.",
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Reason for change (optional)"}),
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
        for name in ("new_password1", "new_password2"):
            if name in self.fields:
                self.fields[name].help_text = ""
