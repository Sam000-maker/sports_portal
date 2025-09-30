from __future__ import annotations

from datetime import datetime
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, View

from .models import Venue, VenuePhoto, Booking
from .forms import VenueForm, VenuePhotoForm, BookingForm


# ---- Role helpers ------------------------------------------------------------

def is_admin_like(user) -> bool:
    return bool(getattr(user, "is_staff", False) or getattr(user, "role", "") in {"admin", "staff", "coach"})


class AdminLikeRequired(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_admin_like(self.request.user)


class RoleTemplateMixin:
    """
    Switches template by role *without* changing models or URLs.
    Provide `admin_template` and `student_template` on the view.
    """
    admin_template: str = ""
    student_template: str = ""

    def get_template_names(self):
        if is_admin_like(self.request.user):
            return [self.admin_template]
        return [self.student_template]


# ---- Venue Lists -------------------------------------------------------------

class VenueListView(RoleTemplateMixin, LoginRequiredMixin, ListView):
    model = Venue
    context_object_name = "venues"
    admin_template = "facilities/admin/venue_list.html"
    student_template = "facilities/student/venue_list.html"

    def get_queryset(self):
        qs = Venue.objects.all().prefetch_related(
            Prefetch("photos", queryset=VenuePhoto.objects.only("id", "venue_id", "caption", "image"))
        )
        if not is_admin_like(self.request.user):
            qs = qs.filter(is_active=True)
        return qs.order_by("-is_active", "name")


class VenueListAdminView(VenueListView, AdminLikeRequired):
    admin_template = "facilities/admin/venue_list.html"
    student_template = "facilities/admin/venue_list.html"


class VenueListStudentView(VenueListView, LoginRequiredMixin):
    admin_template = "facilities/student/venue_list.html"
    student_template = "facilities/student/venue_list.html"


# ---- Venue Create / Detail ---------------------------------------------------

class VenueCreateView(AdminLikeRequired, CreateView):
    model = Venue
    form_class = VenueForm
    template_name = "facilities/admin/venue_form.html"
    success_url = reverse_lazy("facilities:venue_list")


class VenueDetailView(RoleTemplateMixin, LoginRequiredMixin, DetailView):
    model = Venue
    context_object_name = "venue"
    admin_template = "facilities/admin/venue_detail.html"
    student_template = "facilities/student/venue_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venue: Venue = self.object
        ctx["upcoming_bookings"] = (
            Booking.objects.filter(venue=venue, end__gte=timezone.now())
            .select_related("created_by")
            .order_by("start")[:50]
        )
        if not is_admin_like(self.request.user):
            ctx["booking_form"] = BookingForm(initial={"venue": self.object}, user=self.request.user)
        return ctx


# Toggle active/inactive (Admin only)
class VenueToggleActiveView(AdminLikeRequired, View):
    def post(self, request, pk: int):
        venue = get_object_or_404(Venue, pk=pk)
        venue.is_active = not venue.is_active
        venue.save(update_fields=["is_active"])
        messages.success(request, f"Venue '{venue.name}' is now {'active' if venue.is_active else 'inactive'}.")
        return redirect("facilities:venue_detail", pk=pk)


# ---- Photos ------------------------------------------------------------------

class VenuePhotoCreateView(AdminLikeRequired, CreateView):
    model = VenuePhoto
    fields = ["image", "caption"]
    template_name = "facilities/admin/venue_photo_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.venue = get_object_or_404(Venue, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["venue"] = self.venue
        return ctx

    def form_valid(self, form):
        form.instance.venue = self.venue
        messages.success(self.request, "Photo uploaded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("facilities:venue_detail", kwargs={"pk": self.venue.pk})


# ---- Bookings ----------------------------------------------------------------

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "facilities/booking_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = Booking.Status.PENDING
        messages.success(self.request, "Booking request submitted and is pending approval.")
        return super().form_valid(form)

    def get_success_url(self):
        venue = self.object.venue
        return reverse("facilities:venue_detail", kwargs={"pk": venue.pk}) if venue else reverse("facilities:venue_list")


class BookingListAdminView(AdminLikeRequired, ListView):
    model = Booking
    template_name = "facilities/admin/booking_list.html"
    context_object_name = "bookings"

    def get_queryset(self):
        qs = Booking.objects.select_related("venue", "created_by").order_by("-start")
        # Filters: ?status=APPROVED|PENDING|REJECTED, ?venue=<id>, ?from=YYYY-MM-DD, ?to=YYYY-MM-DD
        status = self.request.GET.get("status")
        if status in dict(Booking.Status.choices):
            qs = qs.filter(status=status)
        venue_id = self.request.GET.get("venue")
        if venue_id and venue_id.isdigit():
            qs = qs.filter(venue_id=int(venue_id))
        date_from = self.request.GET.get("from")
        date_to = self.request.GET.get("to")
        if date_from:
            qs = qs.filter(start__date__gte=date_from)
        if date_to:
            qs = qs.filter(end__date__lte=date_to)
        return qs


class MyBookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = "facilities/student/my_booking_list.html"
    context_object_name = "bookings"

    def get_queryset(self):
        return (
            Booking.objects.filter(created_by=self.request.user)
            .exclude(status=Booking.Status.REJECTED)
            .select_related("venue")
            .order_by("-start")
        )


# Admin: approve / reject

class BookingApproveView(AdminLikeRequired, View):
    def post(self, request, pk: int):
        booking = get_object_or_404(Booking, pk=pk)
        booking.status = Booking.Status.APPROVED
        booking.decided_by = request.user
        booking.decided_at = timezone.now()
        booking.save(update_fields=["status", "decided_by", "decided_at"])
        messages.success(request, f"Booking for '{booking.venue.name}' approved.")
        return redirect(request.POST.get("next") or reverse("facilities:booking_list_admin"))


class BookingRejectView(AdminLikeRequired, View):
    def post(self, request, pk: int):
        booking = get_object_or_404(Booking, pk=pk)
        booking.status = Booking.Status.REJECTED
        booking.decided_by = request.user
        booking.decided_at = timezone.now()
        booking.save(update_fields=["status", "decided_by", "decided_at"])
        messages.info(request, f"Booking for '{booking.venue.name}' rejected.")
        return redirect(request.POST.get("next") or reverse("facilities:booking_list_admin"))
