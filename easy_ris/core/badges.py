"""Badge callbacks for the admin interface."""

from easy_ris.core.models import Triage, Report


def triage_badge_callback(request):
    """Return the number of pending triages."""
    count = Triage.objects.filter(status="Pending").count()
    return count if count > 0 else 0


def report_badge_callback(request):
    """Return the number of reported scans that need reporting."""
    count = Report.objects.filter(status="Completed").count()
    return count if count > 0 else 0
