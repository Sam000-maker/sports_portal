# players/views.py
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, FormView, TemplateView

from .forms import PlayerRegistrationForm, PlayerProfileUpdateForm, TeamInviteForm, GalleryForm
from .models import PlayerProfile, Team, TeamMembership, Gallery, Like

User = get_user_model()


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow access only to users with role='student'."""
    def test_func(self):
        Roles = getattr(User, "Roles", None)
        student_value = getattr(Roles, "STUDENT", "student")
        return self.request.user.is_authenticated and getattr(self.request.user, "role", "") == student_value

    def handle_no_permission(self):
        messages.error(self.request, "Only student accounts can access this page.")
        return redirect("accounts:profile")


# -- Profile Views --

class PlayerRegisterView(FormView):
    template_name = "players/register.html"
    form_class = PlayerRegistrationForm
    success_url = reverse_lazy("players:profile_edit")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Registration successful! Please complete your profile.")
        return super().form_valid(form)


class ProfileUpdateView(StudentRequiredMixin, View):
    template_name = "players/profile_edit.html"

    def _ensure_profile(self, user):
        profile, _ = PlayerProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": (user.get_full_name() or user.username)},
        )
        return profile

    def get(self, request):
        profile = self._ensure_profile(request.user)
        form = PlayerProfileUpdateForm(instance=profile)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        profile = self._ensure_profile(request.user)
        form = PlayerProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("players:profile_edit")
        return render(request, self.template_name, {"form": form})


# -- Team Views --

class TeamListView(StudentRequiredMixin, ListView):
    template_name = "players/team_list.html"
    context_object_name = "teams"

    def get_queryset(self):
        user = self.request.user
        return (
            Team.objects
            .filter(Q(created_by=user) | Q(memberships__user=user, memberships__is_approved=True))
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_invites"] = TeamMembership.objects.filter(user=self.request.user, is_approved=False)
        return context


class TeamCreateView(StudentRequiredMixin, CreateView):
    model = Team
    fields = ["name", "sport"]
    template_name = "players/team_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        TeamMembership.objects.create(team=self.object, user=self.request.user, is_approved=True)
        messages.success(self.request, f"Team '{self.object.name}' created successfully.")
        return response

    def get_success_url(self):
        return reverse("players:team_detail", args=[self.object.id])


class TeamDetailView(StudentRequiredMixin, View):
    template_name = "players/team_detail.html"

    def get(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        members = team.memberships.filter(is_approved=True)
        pending = team.memberships.filter(is_approved=False)
        invite_form = TeamInviteForm(team=team) if request.user == team.created_by else None
        user_invited = pending.filter(user=request.user).exists()
        context = {
            "team": team,
            "members": members,
            "pending_invites": pending,
            "invite_form": invite_form,
            "user_invited": user_invited,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        if request.user != team.created_by:
            return redirect("players:team_detail", pk=pk)
        form = TeamInviteForm(request.POST, team=team)
        if form.is_valid():
            invited_user = form.cleaned_data["user"]
            TeamMembership.objects.get_or_create(team=team, user=invited_user, defaults={"is_approved": False})
            messages.success(request, f"Invitation sent to {invited_user.username}.")
            return redirect("players:team_detail", pk=pk)
        members = team.memberships.filter(is_approved=True)
        pending = team.memberships.filter(is_approved=False)
        return render(request, self.template_name, {
            "team": team,
            "members": members,
            "pending_invites": pending,
            "invite_form": form,
            "user_invited": False,
        })


class AcceptInviteView(StudentRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        membership = get_object_or_404(TeamMembership, team=team, user=request.user)
        if not membership.is_approved:
            membership.is_approved = True
            membership.save()
            messages.success(request, f"You have joined team '{team.name}'.")
        return redirect("players:team_detail", pk=pk)


# -- Gallery Views --

class GalleryListView(StudentRequiredMixin, ListView):
    model = Gallery
    template_name = "players/gallery_list.html"
    context_object_name = "photos"
    queryset = Gallery.objects.all().order_by("-uploaded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        liked = Like.objects.filter(user=self.request.user).values_list("photo_id", flat=True)
        context["liked_photos"] = set(liked)
        return context


class GalleryUploadView(StudentRequiredMixin, CreateView):
    model = Gallery
    form_class = GalleryForm
    template_name = "players/gallery_form.html"

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Photo uploaded successfully.")
        return response

    def get_success_url(self):
        return reverse("players:gallery_list")


class GalleryLikeToggle(StudentRequiredMixin, View):
    def post(self, request, pk):
        photo = get_object_or_404(Gallery, pk=pk)
        existing = Like.objects.filter(photo=photo, user=request.user)
        if existing.exists():
            existing.delete()
        else:
            Like.objects.create(photo=photo, user=request.user)
        return redirect("players:gallery_list")


# -- Dashboard --

class PlayerDashboardView(StudentRequiredMixin, TemplateView):
    template_name = "players/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Ensure profile exists
        profile, _ = PlayerProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": (user.get_full_name() or user.username)},
        )

        # Teams: owner or approved member
        teams_qs = (
            Team.objects
            .filter(Q(created_by=user) | Q(memberships__user=user, memberships__is_approved=True))
            .select_related("sport", "created_by")
            .prefetch_related("memberships__user")
            .distinct()
        )

        # Pending invites for current user
        pending_invites = (
            TeamMembership.objects
            .filter(user=user, is_approved=False)
            .select_related("team", "team__sport", "team__created_by")
        )

        # Gallery feed: newest first, with like counts
        gallery_qs = (
            Gallery.objects
            .select_related("uploaded_by")
            .annotate(like_count=Count("likes"))
            .order_by("-uploaded_at")[:12]
        )

        # Photos liked by current user (for UI state)
        liked_ids = set(Like.objects.filter(user=user).values_list("photo_id", flat=True))

        # Quick “scoreboard” counts (wire these to real apps later)
        ctx["stats"] = {
            "athletes": PlayerProfile.objects.count(),
            "teams": Team.objects.count(),
            "matches": 132,  # TODO: replace with tournaments
            "venues": 12,    # TODO: replace with facilities
        }

        # FIX A: Interests come from the view, not a template split filter
        ctx["interests"] = [
            "Training", "Fixtures", "Stats", "Photos",
            "Events", "Fitness", "Wellness", "Coaching",
        ]

        ctx.update({
            "profile": profile,
            "teams": teams_qs,
            "pending_invites": pending_invites,
            "photos": gallery_qs,
            "liked_photos": liked_ids,
        })
        return ctx
