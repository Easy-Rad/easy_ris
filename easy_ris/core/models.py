from django.db import models
from django.utils import timezone


class Patient(models.Model):
    NHI = models.CharField(max_length=10, unique=True)  # National Health Index number
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    contact = models.CharField(max_length=15, blank=True)

    def save(self, *args, **kwargs):
        self.NHI = self.NHI.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.NHI})"

    def __repr__(self):
        return f"Patient({self.first_name}, {self.last_name}, {self.NHI})"


class Modality(models.TextChoices):
    XR = "XR", "X-Ray"
    CT = "CT", "CT"
    MRI = "MRI", "MRI"
    US = "US", "Ultrasound"
    NM = "NM", "Nuclear Medicine"
    FL = "FL", "Fluoroscopy"


class Request(models.Model):
    class Urgency(models.TextChoices):
        IMMEDIATE = "Immediate", "Immediate"
        ONE_HOUR = "<1 hour", "<1 hour"
        FOUR_HOURS = "<4 hours", "<4 hours"
        TWENTY_FOUR_HOURS = "<24 hours", "<24 hours"
        TWO_WEEKS = "<2 weeks", "<2 weeks"
        FOUR_WEEKS = "<4 weeks", "<4 weeks"
        PLANNED = "Planned", "Planned"

    class State(models.TextChoices):
        PENDING = "Pending", "Pending"
        TRIAGED = "Triaged", "Triaged"
        WAITLISTED = "Waitlisted", "Waitlisted"
        SCHEDULED = "Scheduled", "Scheduled"
        COMPLETED = "Completed", "Completed"
        REPORTED = "Reported", "Reported"
        CANCELLED = "Cancelled", "Cancelled"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    patient_type = models.CharField(
        max_length=10,
        choices=[
            ("ED", "Emergency"),
            ("INP", "Inpatient"),
            ("OUT", "Outpatient"),
            ("PRI", "Private"),
            ("ACC", "ACC"),
        ],
    )

    accession_number = models.CharField(
        max_length=20, unique=True, verbose_name="Accession"
    )  # e.g. "CT-123456"
    modality = models.CharField(max_length=10, choices=Modality.choices)
    clinical_info = models.TextField()  # e.g. "Abdominal pain"
    study_requested = models.CharField(max_length=50)  # e.g. "CT Abdomen"
    urgency = models.CharField(max_length=10, choices=Urgency.choices)

    referrer_name = models.CharField(max_length=50)  # e.g. "Dr. Smith"
    referrer_team = models.CharField(max_length=50)  # e.g. "Cardiology"
    referrer_contact = models.CharField(
        max_length=50,
        blank=True,
    )  # e.g. "0212345678" or "8891"
    received_datetime = models.DateTimeField(auto_now_add=True)

    triaged_protocol = models.CharField(
        max_length=50,
        blank=True,
    )  # e.g. "CTA Abdomen Bleed"
    triaged_category = models.CharField(
        max_length=50,
        choices=Urgency.choices,
        blank=True,
    )
    triaged_by = models.CharField(max_length=50, blank=True)  # e.g. "Dr. Dykes"
    triaged_datetime = models.DateTimeField(blank=True, null=True)

    appointment_datetime = models.DateTimeField(null=True, blank=True)
    appointment_location = models.CharField(max_length=50, blank=True)

    study_completed_datetime = models.DateTimeField(null=True, blank=True)
    tech_initials = models.CharField(max_length=50, blank=True)

    report = models.TextField(blank=True)
    rad_initials = models.CharField(max_length=50, blank=True)
    results_notified = models.CharField(max_length=50, blank=True)
    results_notified_datetime = models.DateTimeField(null=True, blank=True)

    tech_comments = models.TextField(blank=True)
    radiologist_comments = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.PENDING,
    )

    def save(self, *args, **kwargs):
        if self.status == self.State.COMPLETED and not self.study_completed_datetime:
            self.study_completed_datetime = timezone.now()

        # If appointment is set and status is Triaged, change to Scheduled
        if self.appointment_datetime and self.status == self.State.TRIAGED:
            self.status = self.State.SCHEDULED

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient} - {self.modality} ({self.received_datetime.strftime('%Y-%m-%d %H:%M')})"

    def __repr__(self):
        return f"Request({self.patient}, {self.modality}, {self.received_datetime.strftime('%Y-%m-%d %H:%M')})"

    def get_inline_title(self):
        """
        Return the title for the inline admin form.
        """
        return f"{self.accession_number}"


class Referral(Request):
    class Meta:
        proxy = True
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"


class Visit(Request):
    class Meta:
        proxy = True
        verbose_name = "Visit"
        verbose_name_plural = "Visits"


class Report(Request):
    class Meta:
        proxy = True
        verbose_name = "Report"
        verbose_name_plural = "Reports"


class Triage(Request):
    class Meta:
        proxy = True
        verbose_name = "Triage"
        verbose_name_plural = "Triages"
