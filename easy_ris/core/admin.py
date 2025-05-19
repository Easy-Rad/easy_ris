from django import forms
from django.contrib import admin, messages
from django.contrib.admin.filters import ChoicesFieldListFilter
from django.db.models import CharField, Count, Max
from django.db.models.functions import Cast, Substr
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin, ExportActionModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, SelectableFieldsExportForm
from unfold.decorators import action, display
from unfold.sections import TableSection, TemplateSection
from unfold.widgets import UnfoldAdminTextareaWidget, UnfoldAdminTextInputWidget

from easy_ris.core.models import (
    Modality,
    Patient,
    Referral,
    Report,
    Request,
    Triage,
    Visit,
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
BASE_STYLE = "padding: 0.15rem 0.35rem; font-size: 0.7rem; font-weight: 500; border-radius: 9999px; border-width: 1px; white-space: nowrap; display: inline-block;"


class HorizontalChoicesFieldListFilter(ChoicesFieldListFilter):
    horizontal = True  # Enable horizontal layout


class ReferralAdminForm(forms.ModelForm):
    accession_override = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional: Only use if there is an existing accession number",
        widget=UnfoldAdminTextInputWidget(),
    )
    tech_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}),
        required=False,
    )
    clinical_info = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )

    class Meta:
        model = Referral
        fields = "__all__"


class VisitAdminForm(forms.ModelForm):
    tech_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}),
        help_text="Patient location, procedure code, etc.",
        required=False,
    )
    clinical_info = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )

    class Meta:
        model = Visit
        fields = "__all__"


class ReportAdminForm(forms.ModelForm):
    tech_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )
    radiologist_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )
    clinical_info = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )

    class Meta:
        model = Report
        fields = "__all__"


class TriageAdminForm(forms.ModelForm):
    tech_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )
    radiologist_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )
    clinical_info = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )

    class Meta:
        model = Triage
        fields = "__all__"


class RequestAdminForm(forms.ModelForm):
    tech_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )
    radiologist_comments = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )
    clinical_info = forms.CharField(
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}), required=False
    )

    class Meta:
        model = Request
        fields = "__all__"


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
    form = ReferralAdminForm
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
                    ("urgency", "accession_override"),
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Hide the actual accession_number field
        if "accession_number" in form.base_fields:
            form.base_fields["accession_number"].widget = forms.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        # Change status from Pending to Waitlisted only for XR modality
        if obj.status == Request.State.PENDING and obj.modality == Modality.XR:
            obj.status = Request.State.WAITLISTED

        if not change:  # Only for new objects
            # Check if there's an override
            accession_override = form.cleaned_data.get("accession_override")
            if accession_override:
                obj.accession_number = accession_override
            else:
                # First save to get the ID
                super().save_model(request, obj, form, change)
                # Then update with the generated accession number
                obj.accession_number = f"TEMP-{obj.id}-{obj.modality}"
                # Save again with the new accession number
                super().save_model(request, obj, form, change)
                return
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient")

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )


@admin.register(Visit)
class VisitAdmin(ModelAdmin):
    form = VisitAdminForm

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
        "tech_initials",
        "tech_comments",
    ]

    @action(
        description="Complete study",
        icon="check_box",
        url_path="complete-visit",
    )
    def complete_visit(self, request: HttpRequest, object_id: int):
        obj = self.get_object(request, object_id)
        if obj.status == Request.State.SCHEDULED:
            obj.status = Request.State.COMPLETED
            obj.study_completed_datetime = timezone.now()
            obj.save()
            messages.success(
                request, f"Visit {obj.accession_number} has been marked as completed."
            )
            return self.response_change(request, obj)
        else:
            messages.error(
                request,
                f"Visit {obj.accession_number} must be in Scheduled status to be completed.",
            )
            return HttpResponseRedirect(
                request.META.get("HTTP_REFERER", reverse("admin:core_visit_changelist"))
            )

    actions_row = [
        "complete_visit",
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
        "patient_date_of_birth",
        "patient_type",
        "accession_number",
        "modality",
        "study_requested",
        "triaged_protocol",
        "triaged_category",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("patient", "patient_date_of_birth"),
                    ("patient_type", "accession_number"),
                    ("modality", "study_requested"),
                    ("triaged_protocol", "triaged_category"),
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

    def patient_date_of_birth(self, obj):
        return obj.patient.date_of_birth if obj.patient else None

    patient_date_of_birth.short_description = "Date of Birth"


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    form = ReportAdminForm

    def get_queryset(self, request):
        # Only display reports with status Reported or Completed
        qs = super().get_queryset(request)
        return qs.filter(status__in=["Reported", "Completed"]).select_related("patient")

    def save_model(self, request, obj, form, change):
        # If status is Completed, update it to Reported
        if obj.status == Request.State.COMPLETED:
            obj.status = Request.State.REPORTED
        super().save_model(request, obj, form, change)

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

    full_width = True
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
    form = TriageAdminForm
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
class RequestAdmin(ModelAdmin, ImportExportModelAdmin):
    form = RequestAdminForm
    export_form_class = SelectableFieldsExportForm
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
        (
            "Basic Information",
            {
                "fields": (
                    ("patient", "patient_type"),
                    ("accession_number", "modality"),
                    ("study_requested", "urgency"),
                    "clinical_info",
                    "status",
                ),
            },
        ),
        (
            "Referrer Information",
            {
                "fields": (
                    ("referrer_name", "referrer_team"),
                    "referrer_contact",
                ),
                "classes": ["tab"],
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
                "classes": ["tab"],
            },
        ),
        (
            "Appointment Information",
            {
                "fields": (
                    "appointment_datetime",
                    "appointment_location",
                ),
                "classes": ["tab"],
            },
        ),
        (
            "Study Information",
            {
                "fields": (
                    "study_completed_datetime",
                    "tech_initials",
                ),
                "classes": ["tab"],
            },
        ),
        (
            "Report Information",
            {
                "fields": (
                    "report",
                    "rad_initials",
                    "results_notified",
                    "results_notified_datetime",
                ),
                "classes": ["tab"],
            },
        ),
        (
            "Comments",
            {
                "fields": (
                    "tech_comments",
                    "radiologist_comments",
                ),
                "classes": ["tab"],
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient")

    @display(description="Status")
    def display_status(self, obj):
        style = f"{BASE_STYLE} {STATUS_STYLES.get(obj.status, '')}"
        return format_html(
            '<span style="{}">&#8226; {}</span>', style, obj.get_status_display()
        )
