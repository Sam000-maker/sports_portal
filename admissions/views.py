#admissions/views.py
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
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
    ApplicationDocumentFormSet,
    StartAdmissionForm,
    ExtendAdmissionForm,
    StopAdmissionForm,
    SportsQuotaAdminForm,   # full admin edit form
)
from .models import SportsQuotaApplication, ApplicationDocument, ApplicationCycle
from .permissions import is_admin_like
from .services import start_admissions, stop_admissions, extend_admissions


# -------------------------------
# Applicant views
# -------------------------------
class ApplicationListView(LoginRequiredMixin, ListView):
    model = SportsQuotaApplication
    paginate_by = 20
    template_name = "admissions/application_list.html"
    context_object_name = "applications"

    def _parse_cycle_query(self, raw: str | None) -> int | None:
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
        qs = (
            SportsQuotaApplication.objects
            .select_related("applicant", "cycle")
            .prefetch_related("documents")
            .order_by("-submitted_at")
        )

        if is_admin_like(self.request.user):
            status = self.request.GET.get("status")
            sport = self.request.GET.get("sport")
            raw_cycle = self.request.GET.get("cycle_id") or self.request.GET.get("cycle")
            if status:
                qs = qs.filter(status=status)
            if sport:
                qs = qs.filter(sport__iexact=sport)
            if raw_cycle:
                pk = self._parse_cycle_query(raw_cycle)
                if pk:
                    qs = qs.filter(cycle_id=pk)
            return qs

        # Regular users only see their own
        return qs.filter(applicant_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Build the dropdown of cycles for filtering (no invalid .only('public_id'))
        if is_admin_like(self.request.user):
            cycles_qs = (
                ApplicationCycle.objects.only("id", "name", "start_date")
                .order_by("-start_date", "-id")
            )
        else:
            my_cycle_ids = (
                SportsQuotaApplication.objects
                .filter(applicant_id=self.request.user.id)
                .values_list("cycle_id", flat=True)
            )
            cycles_qs = (
                ApplicationCycle.objects.filter(id__in=my_cycle_ids)
                .only("id", "name", "start_date")
                .order_by("-start_date", "-id")
            )

        ctx["available_cycles"] = cycles_qs
        ctx["filters"] = {
            "sport": self.request.GET.get("sport", ""),
            "status": self.request.GET.get("status", ""),
            "cycle_id": self.request.GET.get("cycle_id", ""),
        }
        return ctx


class ApplicationCreateView(LoginRequiredMixin, View):
    """
    Single-page application with inline documents.
    Validates cycle window, binds applicant, saves atomically.
    """
    template_name = "admissions/application_form.html"
    success_url = reverse_lazy("admissions:my_applications")

    def _live_cycles_qs(self):
        today = timezone.localdate()
        return ApplicationCycle.objects.filter(
            is_active=True, start_date__lte=today, end_date__gte=today
        )

    def dispatch(self, request, *args, **kwargs):
        if not self._live_cycles_qs().exists():
            messages.error(request, "Admissions are currently closed.")
            return redirect("admissions:my_applications")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = SportsQuotaApplicationForm()
        form.fields["cycle"].queryset = self._live_cycles_qs()
        formset = ApplicationDocumentFormSet()
        return render(request, self.template_name, {"form": form, "formset": formset})

    @transaction.atomic
    def post(self, request):
        form = SportsQuotaApplicationForm(request.POST, request.FILES)
        form.fields["cycle"].queryset = self._live_cycles_qs()

        # Bind a temporary instance for the formset so validation (min_num) works
        temp_instance = SportsQuotaApplication(applicant=request.user)
        formset = ApplicationDocumentFormSet(request.POST, request.FILES, instance=temp_instance)

        if form.is_valid() and formset.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.status = SportsQuotaApplication.Status.SUBMITTED
            application.save()

            formset.instance = application
            formset.save()

            messages.success(request, "Application submitted with documents.")
            return redirect(self.success_url)

        return render(request, self.template_name, {"form": form, "formset": formset})


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = SportsQuotaApplication
    template_name = "admissions/application_detail.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("cycle", "applicant").prefetch_related("documents")
        if is_admin_like(self.request.user):
            return qs
        return qs.filter(applicant_id=self.request.user.id)


class DocumentUploadView(LoginRequiredMixin, View):
    """
    Kept for admins to append files if needed after submission.
    Regular users use the single-page create flow; further edits are blocked when locked.
    """
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

    def get(self, request, pk):
        formset = ApplicationDocumentFormSet(instance=self.application)
        return render(request, self.template_name, {"application": self.application, "formset": formset})

    @transaction.atomic
    def post(self, request, pk):
        formset = ApplicationDocumentFormSet(request.POST, request.FILES, instance=self.application)
        if formset.is_valid():
            formset.save()
            messages.success(self.request, "Documents updated.")
            return redirect("admissions:application_detail", pk=self.application.pk)
        return render(request, self.template_name, {"application": self.application, "formset": formset})


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
    Admin review/edit page. Edits the full application AND manages documents inline.
    """
    model = SportsQuotaApplication
    form_class = SportsQuotaAdminForm
    template_name = "admissions/application_review_form.html"
    context_object_name = "object"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["cycle"].queryset = ApplicationCycle.objects.all()
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        if "doc_formset" in kwargs:
            ctx["doc_formset"] = kwargs["doc_formset"]
        else:
            ctx["doc_formset"] = ApplicationDocumentFormSet(
                instance=obj,
                prefix="docs",
            )
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        doc_formset = ApplicationDocumentFormSet(
            request.POST, request.FILES, instance=self.object, prefix="docs"
        )
        if form.is_valid() and doc_formset.is_valid():
            return self.forms_valid(form, doc_formset)
        else:
            return self.forms_invalid(form, doc_formset)

    @transaction.atomic
    def forms_valid(self, form, doc_formset):
        obj: SportsQuotaApplication = form.save(commit=False)
        action = self.request.POST.get("action")
        notes = form.cleaned_data.get("review_notes") or ""
        obj.reviewer = self.request.user

        # Save the main form first
        obj.save()
        form.save_m2m()

        # Save documents (add/replace/delete)
        doc_formset.save()

        # Handle decision buttons
        if action in {"approve", "reject", "under_review"}:
            if action == "approve":
                obj.status = SportsQuotaApplication.Status.APPROVED
                obj.locked = True
                messages.success(self.request, "Application approved and locked.")
            elif action == "reject":
                obj.status = SportsQuotaApplication.Status.REJECTED
                obj.locked = True
                messages.info(self.request, "Application rejected and locked.")
            else:
                obj.status = SportsQuotaApplication.Status.UNDER_REVIEW
                messages.info(self.request, "Application marked under review.")

            obj.save(update_fields=["status", "locked", "reviewer"])

            if hasattr(obj, "set_status"):
                obj.set_status(obj.status, self.request.user, notes)
        else:
            messages.success(self.request, "Review & documents saved.")

        return redirect(self.get_success_url())

    def forms_invalid(self, form, doc_formset):
        context = self.get_context_data(form=form, doc_formset=doc_formset)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("admissions:application_detail", args=[self.object.pk])


class ApplicationDecisionView(StaffRequiredMixin, DetailView):
    """
    Separate endpoint still supported for quick decisions from the detail view.
    """
    model = SportsQuotaApplication
    template_name = "admissions/application_detail.html"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        action = request.POST.get("action")
        notes = request.POST.get("notes", "")
        with transaction.atomic():
            if action == "approve":
                obj.status = SportsQuotaApplication.Status.APPROVED
                obj.locked = True
                if hasattr(obj, "set_status"):
                    obj.set_status(obj.status, request.user, notes)
                obj.save(update_fields=["status", "locked"])
                messages.success(request, "Application approved.")
            elif action == "reject":
                obj.status = SportsQuotaApplication.Status.REJECTED
                obj.locked = True
                if hasattr(obj, "set_status"):
                    obj.set_status(obj.status, request.user, notes)
                obj.save(update_fields=["status", "locked"])
                messages.info(request, "Application rejected.")
            elif action == "under_review":
                obj.status = SportsQuotaApplication.Status.UNDER_REVIEW
                if hasattr(obj, "set_status"):
                    obj.set_status(obj.status, request.user, notes)
                obj.save(update_fields=["status"])
                messages.info(request, "Marked under review.")
            else:
                messages.error(request, "Unknown action.")
        return redirect("admissions:application_detail", pk=obj.pk)


class AdmissionControlView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "admissions/admin_cycle.html"

    def get_context_data(self, **kwargs):
        """
        Adds:
          - q: search text
          - app_count per cycle (annotate)
          - counts.{live,upcoming,past}
          - live_next_close, upcoming_next_open for summary cards
        """
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        q = (self.request.GET.get("q") or "").strip()
        base = ApplicationCycle.objects.all().annotate(app_count=Count("applications"))

        # Allow searching by name or public id like "CYC-0007" (or plain integer id)
        cond = Q()
        if q:
            cond |= Q(name__icontains=q)
            upper = q.upper()
            if upper.startswith("CYC-"):
                digits = upper.replace("CYC-", "").lstrip("0") or "0"
                try:
                    cond |= Q(id=int(digits))
                except ValueError:
                    pass
            elif q.isdigit():
                cond |= Q(id=int(q))
            base = base.filter(cond)

        live = base.filter(start_date__lte=today, end_date__gte=today).order_by("start_date", "id")
        upcoming = base.filter(start_date__gt=today).order_by("start_date", "id")
        past = base.filter(end_date__lt=today).order_by("-start_date", "-id")

        ctx["q"] = q
        ctx["live_cycles"] = live
        ctx["upcoming_cycles"] = upcoming
        ctx["past_cycles"] = past
        ctx["counts"] = {
            "live": live.count(),
            "upcoming": upcoming.count(),
            "past": past.count(),
        }
        ctx["live_next_close"] = live.order_by("end_date").first()
        ctx["upcoming_next_open"] = upcoming.order_by("start_date").first()
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
                initial["cycle"] = c
            except ApplicationCycle.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        result = start_admissions(name=data["name"], start_date=data["start_date"], end_date=data["end_date"])
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
            messages.info(self.request, f"Admissions closed for cycle “{stopped.name}” (end date set to {stopped.end_date}).")
        else:
            messages.warning(self.request, "Selected cycle was not found.")
        return super().form_valid(form)
