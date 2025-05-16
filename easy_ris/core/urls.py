from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Search URL
    path("", views.SearchView.as_view(), name="search"),
    # Report detail partial URL for HTMX
    path(
        "reports/<int:pk>/partial/",
        views.ReportDetailPartialView.as_view(),
        name="report_detail_partial",
    ),
]
