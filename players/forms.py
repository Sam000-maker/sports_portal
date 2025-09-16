# players/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import PlayerProfile, Sport, Team, Gallery

User = get_user_model()

class PlayerRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, label="Full Name")
    sports = forms.ModelMultipleChoiceField(
        queryset=Sport.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Sports",
    )
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.visible_fields():
            w = field.field.widget
            if not isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                w.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        user.phone = self.cleaned_data.get("phone")

        # Use enum to set role to STUDENT
        Roles = getattr(User, "Roles", None)
        user.role = getattr(Roles, "STUDENT", "student")

        user.is_active = True
        if commit:
            user.save()
            profile = PlayerProfile.objects.create(
                user=user, full_name=self.cleaned_data["full_name"]
            )
            profile.sports.set(self.cleaned_data["sports"])
            profile.save()
        return user

class PlayerProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = PlayerProfile
        fields = ("full_name", "sports", "bio", "achievements", "stats", "photo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.visible_fields():
            w = field.field.widget
            if not isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                w.attrs['class'] = 'form-control'
        if self.instance and hasattr(self.instance, "user"):
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.email = self.cleaned_data.get("email")
        user.phone = self.cleaned_data.get("phone")
        if commit:
            user.save()
            profile.save()
            profile.sports.set(self.cleaned_data.get("sports"))
        else:
            user.save()
        return profile

class TeamInviteForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),  # set in __init__
        label="Invite student"
    )

    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        Roles = getattr(User, "Roles", None)
        student_value = getattr(Roles, "STUDENT", "student")

        qs = User.objects.filter(role=student_value, is_active=True)
        if team:
            qs = qs.exclude(team_memberships__team=team)
        self.fields['user'].queryset = qs

class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ("image", "caption")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.visible_fields():
            w = field.field.widget
            if not isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                w.attrs['class'] = 'form-control'
