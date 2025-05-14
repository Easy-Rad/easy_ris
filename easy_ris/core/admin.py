from django.contrib import admin
from django.contrib.admin.filters import ChoicesFieldListFilter
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.sections import TableSection, TemplateSection
from django.db.models import Max
from django.db.models.functions import Cast, Substr
from django.db.models import CharField

from easy_ris.core.models import (
    Patient,
    Referral,
    Report,
    Request,
    Triage,
    Visit,
    Modality,
)

# Define status styles
STATUS_STYLES = {
    Request.State.PENDING: "background-color: #fef9c3; color: #854d0e; border-color: #fde047;",
    Request.State.TRIAGED: "background-color: #dbeafe; color: #1e40af; border-color: #93c5fd;",
    Request.State.WAITLISTED: "background-color: #f3e8ff; color: #6b21a8; border-color: #d8b4fe;",
    Request.State.SCHEDULED: "background-color: #e0e7ff; color: #3730a3; border-color: #a5b4fc;",
    Request.State.COMPLETED: "background-color: #ccfbf1; color: #115e59; border-color: #5eead4;",
    Request.State.REPORTED: "background-color: #dcfce7; color: #166534; border-color: #86efac;",
    Request.State.CANCELLED: "background-color: #fee2e2; color: #991b1b; border-color: #fca5a5;",
}
BASE_STYLE = "padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 500; border-radius: 9999px; border-width: 1px;"


class HorizontalChoicesFieldListFilter(ChoicesFieldListFilter):
    horizontal = True  # Enable horizontal layout


@admin.register(Patient)
class PatientModelAdmin(ModelAdmin):

    list_display = [
        "first_name",
        "last_name",
        "NHI",
        "date_of_birth",
        "contact",
    ]
    search_fields = ["first_name", "last_name", "NHI"]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("NHI", "date_of_birth"),
                    ("first_name", "last_name"),
                    "contact",
                ]
            },
        ),
    ]


@admin.register(Referral)
class ReferralAdmin(ModelAdmin):
    ordering = ["-received_datetime"]
    autocomplete_fields = ["patient"]
    list_filter_sheet = False

    list_display = [
        "patient",
        "accession_number",
        "modality",
        "study_requested",
        "urgency",
        "referrer_team",
        "display_status",
        "received_datetime",
    ]

    list_filter = [
        "status",
    ]

    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__NHI",
        "accession_number",
    ]

    fieldsets = (
        ("Patient Information", {"fields": (("patient", "patient_type"),)}),
        (
            "Referral Details",
            {
                "fields": (
                    ("urgency", "accession_number"),
                    ("modality", "study_requested"),
                    "clinical_info",
                )
            },
        ),
        (
            "Referrer Information",
            {"fields": (("referrer_name", "referrer_team", "referrer_contact"),)},
        ),
        ("Metadata", {"fields": ("status", "tech_comments")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient")

    def get_next_temp_accession_number(self):
        """Generate the next temporary accession number in the format TEMP-X"""
        # Get the highest existing TEMP number
        last_temp = (
            self.model.objects.filter(accession_number__startswith="TEMP-")
            .annotate(
                temp_num=Cast(
                    Substr("accession_number", 6),  # Extract number after 'TEMP-'
                    output_field=CharField(),
                )
            )
            .aggregate(max_num=Max("temp_num"))["max_num"]
        )

        # If no TEMP numbers exist yet, start with 1
        if last_temp is None:
            return "TEMP-1"

        # Otherwise increment the last number
        try:
            next_num = int(last_temp) + 1
            return f"TEMP-{next_num}"
        except ValueError:
            # If there's any issue with the number format, start with 1
            return "TEMP-1"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # Only set default for new objects
            form.base_fields["accession_number"].initial = (
                self.get_next_temp_accession_number()
            )
        return form

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )


@admin.register(Visit)
class VisitAdmin(ModelAdmin):
    def get_queryset(self, request):
        # Only display visits with status Waitlisted, Scheduled, or Completed
        qs = super().get_queryset(request)
        return qs.filter(
            status__in=["Triaged", "Waitlisted", "Scheduled", "Completed", "Reported"]
        ).select_related("patient")

    ordering = ["-appointment_datetime"]
    compressed_fields = True
    list_fullwidth = True

    list_display = [
        "patient",
        "modality",
        "triaged_protocol",
        "display_status",
        "appointment_datetime",
        "appointment_location",
        "study_completed_datetime",
    ]

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )

    list_filter = ["modality", "status"]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__NHI",
        "accession_number",
    ]

    readonly_fields = [
        "patient",
        "patient_type",
        "accession_number",
        "modality",
        "study_requested",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("patient", "patient_type"),
                    "accession_number",
                    ("modality", "study_requested"),
                    "status",
                    "tech_comments",
                ),
            },
        ),
        (
            "Appointment Information",
            {
                "fields": ("appointment_datetime", "appointment_location"),
                "classes": ["tab"],
            },
        ),
        (
            "Study Completion",
            {
                "fields": ("study_completed_datetime", "tech_initials"),
                "classes": ["tab"],
            },
        ),
    )


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    def get_queryset(self, request):
        # Only display reports with status Reported or Completed
        qs = super().get_queryset(request)
        return qs.filter(status__in=["Reported", "Completed"]).select_related("patient")

    list_display = [
        "patient",
        "accession_number",
        "modality",
        "triaged_protocol",
        "study_completed_datetime",
        "display_status",
        "rad_initials",
        "results_notified",
    ]

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )

    list_filter = ["modality", "status"]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__NHI",
        "accession_number",
    ]
    readonly_fields = [
        "patient",
        "patient_type",
        "accession_number",
        "modality",
        "study_requested",
        "clinical_info",
        "study_completed_datetime",
        "tech_comments",
    ]

    fieldsets = (
        (
            "Study Details",
            {
                "fields": (
                    ("patient", "patient_type", "accession_number"),
                    ("modality", "triaged_protocol", "study_completed_datetime"),
                    "clinical_info",
                )
            },
        ),
        (
            "Report Information",
            {"fields": ("report", "rad_initials", "radiologist_comments")},
        ),
        (
            "Others",
            {"fields": ("status", "results_notified", "results_notified_datetime")},
        ),
    )


@admin.register(Triage)
class TriageAdmin(ModelAdmin):
    compressed_fields = True
    list_fullwidth = True

    list_display = [
        "patient",
        "modality",
        "study_requested",
        "urgency",
        "clinical_info",
        "triaged_protocol",
        "triaged_category",
        "triaged_by",
        "status",  # Keep the actual status field for editing
        "triaged_datetime",
    ]

    list_editable = [
        "triaged_protocol",
        "triaged_category",
        "triaged_by",
        "status",
    ]
    list_filter = ["modality", "urgency", "triaged_category", "status"]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__NHI",
        "accession_number",
    ]

    readonly_fields = [
        "patient",
        "patient_type",
        "accession_number",
        "modality",
        "study_requested",
        "clinical_info",
        "urgency",
        "referrer_name",
        "referrer_team",
        "referrer_contact",
        "received_datetime",
        "triaged_datetime",
    ]

    fieldsets = (
        ("Patient Information", {"fields": ("patient", "patient_type")}),
        (
            "Request Details",
            {
                "fields": (
                    ("referrer_name", "referrer_team", "referrer_contact"),
                    ("modality", "urgency", "accession_number"),
                    "study_requested",
                    "clinical_info",
                )
            },
        ),
        (
            "Triage Information",
            {
                "fields": (
                    "triaged_category",
                    "triaged_protocol",
                    "radiologist_comments",
                    "triaged_by",
                    "status",
                    "triaged_datetime",
                )
            },
        ),
    )

    def get_queryset(self, request):
        # Only exclude XR modality
        qs = super().get_queryset(request)
        return qs.exclude(modality=Modality.XR).select_related("patient")

    def save_model(self, request, obj, form, change):
        from django.utils import timezone

        # Check if this is an existing object being changed
        if change:
            # Get the original object from the database
            original_obj = self.model.objects.get(pk=obj.pk)

            # Check if status is being changed to 'Triaged'
            if original_obj.status != "Triaged" and obj.status == "Triaged":
                # Update triaged_datetime to current time
                obj.triaged_datetime = timezone.now()

        # Continue with the normal save process
        super().save_model(request, obj, form, change)


@admin.register(Request)
class RequestAdmin(ModelAdmin):
    ordering = ["-received_datetime"]
    autocomplete_fields = ["patient"]
    list_filter_sheet = False

    list_display = [
        "patient",
        "accession_number",
        "modality",
        "study_requested",
        "urgency",
        "display_status",
        "received_datetime",
    ]

    list_filter = [
        "status",
        "modality",
        "urgency",
    ]

    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__NHI",
        "accession_number",
    ]

    readonly_fields = [
        "patient",
        "received_datetime",
    ]

    fieldsets = (
        ("Patient Information", {"fields": (("patient", "patient_type"),)}),
        (
            "Request Details",
            {
                "fields": (
                    ("referrer_name", "referrer_team", "referrer_contact"),
                    ("urgency", "accession_number"),
                    ("modality", "study_requested"),
                    "clinical_info",
                )
            },
        ),
        (
            "Triage Information",
            {
                "fields": (
                    "triaged_protocol",
                    "triaged_category",
                    "triaged_by",
                    "triaged_datetime",
                ),
                "classes": ["collapse"],
            },
        ),
        (
            "Appointment Information",
            {
                "fields": (
                    "appointment_datetime",
                    "appointment_location",
                ),
                "classes": ["collapse"],
            },
        ),
        (
            "Study Completion",
            {
                "fields": (
                    "study_completed_datetime",
                    "tech_initials",
                    "tech_comments",
                ),
                "classes": ["collapse"],
            },
        ),
        (
            "Report Information",
            {
                "fields": (
                    "report",
                    "rad_initials",
                    "radiologist_comments",
                    "results_notified",
                    "results_notified_datetime",
                ),
                "classes": ["collapse"],
            },
        ),
        ("Metadata", {"fields": ("status", "received_datetime")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient")

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )
