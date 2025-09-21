from django.urls import path
from . import views

app_name = "facilities"

urlpatterns = [
    path("venues/", views.VenueListView.as_view(), name="venue_list"),
    path("venues/new/", views.VenueCreateView.as_view(), name="venue_new"),
    path("venues/<int:pk>/", views.VenueDetailView.as_view(), name="venue_detail"),
    path("venues/<int:venue_id>/photos/new/", views.VenuePhotoCreateView.as_view(), name="venue_photo_new"),
    path("bookings/new/", views.BookingCreateView.as_view(), name="booking_new"),
]
