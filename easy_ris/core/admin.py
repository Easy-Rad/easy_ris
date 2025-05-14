from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.sections import TableSection, TemplateSection
from unfold.decorators import display

from easy_ris.core.models import Patient, Referral, Report, Request, Triage, Visit

# Define status styles
STATUS_STYLES = {
    Request.State.PENDING: "background-color: #fef9c3; color: #854d0e; border-color: #fde047;",
    Request.State.TRIAGED: "background-color: #dbeafe; color: #1e40af; border-color: #93c5fd;",
    Request.State.WAITLISTED: "background-color: #f3e8ff; color: #6b21a8; border-color: #d8b4fe;",
    Request.State.SCHEDULED: "background-color: #e0e7ff; color: #3730a3; border-color: #a5b4fc;",
    Request.State.COMPLETED: "background-color: #dcfce7; color: #166534; border-color: #86efac;",
    Request.State.REPORTED: "background-color: #ccfbf1; color: #115e59; border-color: #5eead4;",
    Request.State.CANCELLED: "background-color: #fee2e2; color: #991b1b; border-color: #fca5a5;",
}
BASE_STYLE = "padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 500; border-radius: 9999px; border-width: 1px;"


@admin.register(Patient)
class PatientModelAdmin(ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "NHI",
        "date_of_birth",
        "contact",
    ]


@admin.register(Referral)
class ReferralAdmin(ModelAdmin):
    ordering = ["-received_datetime"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient')

    list_display = [
        "patient",
        "accession_number",
        "modality",
        "study_requested",
        "urgency",
        "referrer_name",
        "referrer_team",
        "display_status",
        "received_datetime",
    ]

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )

    list_filter = ["urgency", "modality", "patient_type", "status"]

    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "patient__NHI",
        "accession_number",
    ]

    fieldsets = (
        ("Patient Information", {"fields": ("patient", "patient_type")}),
        (
            "Request Details",
            {
                "fields": (
                    "accession_number",
                    "modality",
                    "study_requested",
                    "clinical_info",
                    "urgency",
                )
            },
        ),
        (
            "Referrer Information",
            {"fields": ("referrer_name", "referrer_team", "referrer_contact")},
        ),
        ("Others", {"fields": ("status", "tech_comments")}),
    )


@admin.register(Visit)
class VisitAdmin(ModelAdmin):
    def get_queryset(self, request):
        # Only display visits with status Waitlisted, Scheduled, or Completed
        qs = super().get_queryset(request)
        return qs.filter(status__in=['Triaged', 'Waitlisted', 'Scheduled', 'Completed']).select_related('patient')
    
    ordering = ["-appointment_datetime"]

    list_display = [
        "patient",
        "accession_number",
        "modality",
        "study_requested",
        "display_status",
        "appointment_datetime",
        "appointment_location",
        "study_completed_datetime",
        "tech_initials",
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
        ("Patient Information", {"fields": ("patient", "patient_type")}),
        (
            "Study Details",
            {
                "fields": ("accession_number", "modality", "study_requested"),
            },
        ),
        (
            "Appointment Information",
            {"fields": ("appointment_datetime", "appointment_location")},
        ),
        (
            "Study Completion",
            {"fields": ("study_completed_datetime", "tech_initials")},
        ),
        ("Others", {"fields": ("status", "tech_comments")}),
    )


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    def get_queryset(self, request):
        # Only display reports with status Reported or Completed
        qs = super().get_queryset(request)
        return qs.filter(status__in=['Reported', 'Completed']).select_related('patient')
    
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
        ("Patient Information", {"fields": ("patient", "patient_type")}),
        (
            "Study Details",
            {
                "fields": (
                    "accession_number",
                    "modality",
                    "study_requested",
                    "clinical_info",
                    "study_completed_datetime",
                )
            },
        ),
        (
            "Report Information",
            {"fields": ("report", "rad_initials", "radiologist_comments")},
        ),
        (
            "Results Notification",
            {"fields": ("results_notified", "results_notified_datetime")},
        ),
        ("Others", {"fields": ("status", "tech_comments")}),
    )


@admin.register(Triage)
class TriageAdmin(ModelAdmin):
    def get_queryset(self, request):
        # Only display triages with status Triaged or Pending
        qs = super().get_queryset(request)
        return qs.filter(status__in=['Triaged', 'Pending']).select_related('patient')
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
                    "accession_number",
                    "modality",
                    "study_requested",
                    "clinical_info",
                    "urgency",
                )
            },
        ),
        (
            "Referrer Information",
            {"fields": ("referrer_name", "referrer_team", "referrer_contact")},
        ),
        (
            "Triage Information",
            {
                "fields": (
                    "triaged_protocol",
                    "triaged_category",
                    "triaged_by",
                    "triaged_datetime",
                    "radiologist_comments",
                    "status",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        from django.utils import timezone

        # Check if this is an existing object being changed
        if change:
            # Get the original object from the database
            original_obj = self.model.objects.get(pk=obj.pk)

            # Check if status is being changed to 'Triaged'
            if original_obj.status != 'Triaged' and obj.status == 'Triaged':
                # Update triaged_datetime to current time
                obj.triaged_datetime = timezone.now()

        # Continue with the normal save process
        super().save_model(request, obj, form, change)
