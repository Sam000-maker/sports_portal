from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    """
    Public registration: username + email + phone.
    Everyone registers as GUEST. No, the public cannot choose 'admin' from a dropdown.
    """
    class Meta:
        model = User
        fields = ("username", "email", "phone")

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
    Standard username/password login.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"})
    )
    password = forms.CharField(
        strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )


class ProfileForm(forms.ModelForm):
    """
    Basic profile edit. Users can’t self-escalate here either.
    """
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "avatar"]

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class AdminRoleUpdateForm(forms.Form):
    """
    Admin-side role change with guardrails:
    - Only admin-like actors may change roles.
    - Non-admin actors can’t assign Admin.
    - Superusers must always have role='admin'.
    - Non-superusers can’t change their own role.
    """
    role = forms.ChoiceField(choices=(), required=True)
    reason = forms.CharField(max_length=255, required=False, help_text="Optional note for audit log.")

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
