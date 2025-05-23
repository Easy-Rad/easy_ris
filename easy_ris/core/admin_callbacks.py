"""Admin callbacks for the admin interface."""

from easy_ris.core.models import Triage, Report, Modality, Request


def triage_badge_callback(request):
    """Return the number of pending triages."""
    count = (
        Triage.objects.filter(status="Pending").exclude(modality=Modality.XR).count()
    )
    return count if count > 0 else 0


def report_badge_callback(request):
    """Return the number of reported scans that need reporting."""
    count = Report.objects.filter(status="Completed").count()
    return count if count > 0 else 0


def visit_badge_callback(request):
    """Return the number of visits in Triaged, Waitlisted, or Scheduled status."""
    count = Request.objects.filter(
        status__in=["Triaged", "Waitlisted", "Scheduled"]
    ).count()
    return count if count > 0 else 0


def dashboard_callback(request, context):
    """
    Callback to prepare custom variables for index template which is used as dashboard
    template.
    """
    # Get request statistics
    total_requests = Request.objects.count()
    pending_requests = Request.objects.filter(status=Request.State.PENDING).count()
    triaged_requests = Request.objects.filter(status=Request.State.TRIAGED).count()
    waitlisted_requests = Request.objects.filter(
        status=Request.State.WAITLISTED
    ).count()
    scheduled_requests = Request.objects.filter(status=Request.State.SCHEDULED).count()
    completed_requests = Request.objects.filter(status=Request.State.COMPLETED).count()
    reported_requests = Request.objects.filter(status=Request.State.REPORTED).count()
    cancelled_requests = Request.objects.filter(status=Request.State.CANCELLED).count()

    # Get recent requests with patient information
    recent_requests = Request.objects.select_related("patient").order_by(
        "-received_datetime"
    )[:10]

    # Add data to context
    context.update(
        {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "triaged_requests": triaged_requests,
            "waitlisted_requests": waitlisted_requests,
            "scheduled_requests": scheduled_requests,
            "completed_requests": completed_requests,
            "reported_requests": reported_requests,
            "cancelled_requests": cancelled_requests,
            "recent_requests": recent_requests,
        }
    )

    return context
