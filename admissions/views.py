# admissions/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    FormView,
    TemplateView,
    View,
)

from .forms import (
    SportsQuotaApplicationForm,
    ApplicationDocumentForm,
    StartAdmissionForm,
    ExtendAdmissionForm,
    StopAdmissionForm,
)
from .models import SportsQuotaApplication, ApplicationDocument, ApplicationCycle
from .permissions import is_admin_like
from .services import start_admissions, stop_admissions, extend_admissions


# -------------------------------
# Applicant views
# -------------------------------
class ApplicationListView(LoginRequiredMixin, ListView):
    """
    Applicants see their own submissions.
    Admins see all, with optional filters via query params.
    """
    model = SportsQuotaApplication
    paginate_by = 20
    template_name = "admissions/application_list.html"

    def _parse_cycle_query(self, raw: str | None) -> int | None:
        """
        Accept either raw PK like "7" or public id like "CYC-0007".
        Return PK int or None.
        """
        if not raw:
            return None
        raw = str(raw).strip().upper()
        if raw.startswith("CYC-"):
            try:
                return int(raw.replace("CYC-", "").lstrip("0") or "0")
            except ValueError:
                return None
        try:
            return int(raw)
        except ValueError:
            return None

    def get_queryset(self):
        qs = SportsQuotaApplication.objects.select_related("applicant", "cycle").all()
        if is_admin_like(self.request.user):
            status = self.request.GET.get("status")
            sport = self.request.GET.get("sport")
            raw_cycle = self.request.GET.get("cycle_id")

            if status:
                qs = qs.filter(status=status)
            if sport:
                qs = qs.filter(sport__iexact=sport)
            if raw_cycle:
                pk = self._parse_cycle_query(raw_cycle)
                if pk:
                    qs = qs.filter(cycle_id=pk)
            return qs
        return qs.filter(applicant=self.request.user)


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    """
    Public application creation. We bind applicant in form_valid and enforce cycle window.
    """
    model = SportsQuotaApplication
    form_class = SportsQuotaApplicationForm
    template_name = "admissions/application_form.html"
    success_url = reverse_lazy("admissions:my_applications")

    def dispatch(self, request, *args, **kwargs):
        today = timezone.localdate()
        has_live = ApplicationCycle.objects.filter(
            is_active=True, start_date__lte=today, end_date__gte=today
        ).exists()
        if not has_live:
            messages.error(request, "Admissions are currently closed.")
            return redirect("admissions:my_applications")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        today = timezone.localdate()
        form.fields["cycle"].queryset = ApplicationCycle.objects.filter(
            is_active=True, start_date__lte=today, end_date__gte=today
        )
        return form

    def form_valid(self, form):
        form.instance.applicant = self.request.user
        messages.success(self.request, "Application submitted.")
        return super().form_valid(form)


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = SportsQuotaApplication
    template_name = "admissions/application_detail.html"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("cycle", "applicant")
            .prefetch_related("documents")
        )
        if is_admin_like(self.request.user):
            return qs
        return qs.filter(applicant=self.request.user)


class DocumentUploadView(LoginRequiredMixin, FormView):
    """
    Post-submission document uploads. Block if locked or not owner/admin.
    """
    form_class = ApplicationDocumentForm
    template_name = "admissions/document_upload.html"

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(SportsQuotaApplication, pk=kwargs["pk"])
        if not (is_admin_like(request.user) or self.application.applicant_id == request.user.id):
            messages.error(request, "Not allowed.")
            return redirect("admissions:my_applications")
        if self.application.locked and not is_admin_like(request.user):
            messages.error(request, "Application is locked and cannot be modified.")
            return redirect("admissions:application_detail", pk=self.application.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ApplicationDocument.objects.create(application=self.application, **form.cleaned_data)
        messages.success(self.request, "Document uploaded.")
        return redirect("admissions:application_detail", pk=self.application.pk)


# -------------------------------
# Admin review and controls
# -------------------------------
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin_like(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Admin access required.")
        return redirect("admissions:my_applications")


class ApplicationReviewUpdateView(StaffRequiredMixin, UpdateView):
    """
    Admin can edit basic fields if needed before making a decision.
    """
    model = SportsQuotaApplication
    form_class = SportsQuotaApplicationForm
    template_name = "admissions/application_review_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Application updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admissions:application_detail", args=[self.object.pk])


class ApplicationDecisionView(StaffRequiredMixin, DetailView):
    """
    Decision endpoints are POSTed to from the detail page.
    """
    model = SportsQuotaApplication
    template_name = "admissions/application_detail.html"  # reuse

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        action = request.POST.get("action")
        notes = request.POST.get("notes", "")
        with transaction.atomic():
            if action == "approve":
                obj.set_status(SportsQuotaApplication.Status.APPROVED, request.user, notes)
                messages.success(request, "Application approved.")
            elif action == "reject":
                obj.set_status(SportsQuotaApplication.Status.REJECTED, request.user, notes)
                messages.info(request, "Application rejected.")
            elif action == "under_review":
                obj.set_status(SportsQuotaApplication.Status.UNDER_REVIEW, request.user, notes)
                messages.info(request, "Marked under review.")
            else:
                messages.error(request, "Unknown action.")
        return redirect("admissions:application_detail", pk=obj.pk)


class AdmissionControlView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    """
    Buckets by dates only so nothing disappears:
      Live     -> start_date <= today <= end_date
      Upcoming -> start_date > today
      Past     -> end_date < today
    'is_active' controls whether applications are allowed, not row visibility.
    """
    template_name = "admissions/admin_cycle.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        ctx["live_cycles"] = (
            ApplicationCycle.objects.filter(start_date__lte=today, end_date__gte=today)
            .order_by("start_date")
        )
        ctx["upcoming_cycles"] = (
            ApplicationCycle.objects.filter(start_date__gt=today)
            .order_by("start_date")
        )
        ctx["past_cycles"] = (
            ApplicationCycle.objects.filter(end_date__lt=today)
            .order_by("-start_date")
        )
        return ctx


class StartAdmissionView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = StartAdmissionForm
    template_name = "admissions/admin_cycle_start.html"
    success_url = reverse_lazy("admissions:admin_cycle")

    def get_initial(self):
        initial = super().get_initial()
        cid = self.request.GET.get("cycle")
        if cid:
            try:
                c = ApplicationCycle.objects.get(pk=cid)
                initial["cycle"] = c  # only if your form supports it
            except ApplicationCycle.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        result = start_admissions(
            name=data["name"],
            start_date=data["start_date"],
            end_date=data["end_date"],
        )
        verb = "created" if result.created else "reactivated"
        messages.success(self.request, f"Admissions {verb} for cycle “{result.cycle.name}”.")
        return super().form_valid(form)


class ExtendAdmissionView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = ExtendAdmissionForm
    template_name = "admissions/admin_cycle_extend.html"
    success_url = reverse_lazy("admissions:admin_cycle")

    def get_initial(self):
        initial = super().get_initial()
        cid = self.request.GET.get("cycle")
        if cid:
            try:
                initial["cycle"] = ApplicationCycle.objects.get(pk=cid)
            except ApplicationCycle.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        cycle = form.cleaned_data["cycle"]
        new_end_date = form.cleaned_data["new_end_date"]

        extend_admissions(cycle_id=cycle.pk, new_end_date=new_end_date)
        cycle.refresh_from_db(fields=["start_date", "end_date", "is_active"])

        today = timezone.localdate()
        if cycle.start_date <= today <= cycle.end_date and not cycle.is_active:
            cycle.is_active = True
            cycle.save(update_fields=["is_active"])
            messages.success(self.request, f"Extended and reactivated “{cycle.name}” to {cycle.end_date}.")
        else:
            messages.success(self.request, f"Extended “{cycle.name}” to {cycle.end_date}.")
        return super().form_valid(form)


class StopAdmissionView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = StopAdmissionForm
    template_name = "admissions/admin_cycle_stop.html"
    success_url = reverse_lazy("admissions:admin_cycle")

    def get_initial(self):
        """
        Prefill the selected cycle from ?cycle=<id> if present.
        """
        initial = super().get_initial()
        cid = self.request.GET.get("cycle")
        if cid:
            try:
                initial["cycle"] = ApplicationCycle.objects.get(pk=cid)
            except ApplicationCycle.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        cycle = form.cleaned_data["cycle"]
        stopped = stop_admissions(cycle_id=cycle.pk)
        if stopped:
            messages.info(
                self.request,
                f"Admissions closed for cycle “{stopped.name}” (end date set to {stopped.end_date})."
            )
        else:
            messages.warning(self.request, "Selected cycle was not found.")
        return super().form_valid(form)
