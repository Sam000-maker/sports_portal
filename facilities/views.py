from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView

from .models import Venue, VenuePhoto, Booking
from .forms import VenueForm, VenuePhotoForm, BookingForm

def is_admin_like(user) -> bool:
    return bool(getattr(user, "is_staff", False) or getattr(user, "role", "") in {"admin", "staff", "coach"})

class AdminLikeRequired(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_admin_like(self.request.user)

class VenueListView(LoginRequiredMixin, ListView):
    model = Venue
    template_name = "facilities/venue_list.html"
    context_object_name = "venues"

class VenueCreateView(AdminLikeRequired, CreateView):
    model = Venue
    form_class = VenueForm
    template_name = "facilities/venue_form.html"
    success_url = reverse_lazy("facilities:venue_list")

class VenueDetailView(LoginRequiredMixin, DetailView):
    model = Venue
    template_name = "facilities/venue_detail.html"
    context_object_name = "venue"

class VenuePhotoCreateView(AdminLikeRequired, CreateView):
    model = VenuePhoto
    form_class = VenuePhotoForm
    template_name = "facilities/venue_photo_form.html"
    def form_valid(self, form):
        venue = get_object_or_404(Venue, pk=self.kwargs["venue_id"])
        form.instance.venue = venue
        messages.success(self.request, "Photo added.")
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy("facilities:venue_detail", kwargs={"pk": self.kwargs["venue_id"]})

class BookingCreateView(AdminLikeRequired, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "facilities/booking_form.html"
    success_url = reverse_lazy("facilities:venue_list")
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Booking created.")
        return super().form_valid(form)
