# admissions/admin.py
from django.contrib import admin
from .models import ApplicationCycle, SportsQuotaApplication, ApplicationDocument

@admin.register(ApplicationCycle)
class ApplicationCycleAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(SportsQuotaApplication)
class SportsQuotaApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "applicant", "sport", "level", "status", "cycle", "submitted_at", "locked")
    list_filter = ("status", "level", "sport", "cycle", "locked")
    search_fields = ("applicant__username", "sport")
    autocomplete_fields = ("applicant", "reviewer")

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ("application", "doc_type", "uploaded_at")
    list_filter = ("doc_type", "uploaded_at")
    search_fields = ("application__sport",)
