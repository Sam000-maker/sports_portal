from django.urls import path
from . import views

app_name = "facilities"

urlpatterns = [
    # Lists & detail
    path("venues/", views.VenueListView.as_view(), name="venue_list"),
    path("venues/new/", views.VenueCreateView.as_view(), name="venue_new"),
    path("venues/<int:pk>/", views.VenueDetailView.as_view(), name="venue_detail"),

    # Optional explicit splits
    path("a/venues/", views.VenueListAdminView.as_view(), name="venue_list_admin"),
    path("s/venues/", views.VenueListStudentView.as_view(), name="venue_list_student"),

    # Photos
    path("venues/<int:pk>/photos/new/", views.VenuePhotoCreateView.as_view(), name="venue_photo_new"),

    # Venue management
    path("venues/<int:pk>/toggle-active/", views.VenueToggleActiveView.as_view(), name="venue_toggle_active"),

    # Bookings
    path("bookings/new/", views.BookingCreateView.as_view(), name="booking_new"),
    path("bookings/admin/", views.BookingListAdminView.as_view(), name="booking_list_admin"),
    path("bookings/mine/", views.MyBookingListView.as_view(), name="my_booking_list"),

    # Booking decisions
    path("bookings/<int:pk>/approve/", views.BookingApproveView.as_view(), name="booking_approve"),
    path("bookings/<int:pk>/reject/", views.BookingRejectView.as_view(), name="booking_reject"),
]
