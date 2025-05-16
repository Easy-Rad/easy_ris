from django.shortcuts import render
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from .models import Patient, Request, Report


class SearchView(LoginRequiredMixin, View):
    template_name = "core/search.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        nhi = request.POST.get("nhi", "").strip().upper()
        if nhi:
            try:
                patient = Patient.objects.get(NHI=nhi)
                requests = Request.objects.filter(patient=patient).order_by(
                    "-received_datetime"
                )
                return render(
                    request,
                    self.template_name,
                    {"patient": patient, "requests": requests, "nhi": nhi},
                )
            except Patient.DoesNotExist:
                return render(
                    request,
                    self.template_name,
                    {"error": f"No patient found with NHI: {nhi}", "nhi": nhi},
                )
        return render(request, self.template_name)


class ReportDetailPartialView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "core/report_detail_partial.html"
    context_object_name = "report"
