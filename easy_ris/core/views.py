from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Patient, Referral, Triage, Visit, Report

# Patient Views
class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'core/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Add any filtering logic here if needed
        return queryset.order_by('last_name', 'first_name')


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = 'core/patient_detail.html'
    context_object_name = 'patient'


# Referral Views
class ReferralListView(LoginRequiredMixin, ListView):
    model = Referral
    template_name = 'core/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Display only pending/new referrals
        return queryset.order_by('-received_datetime')


class ReferralDetailView(LoginRequiredMixin, DetailView):
    model = Referral
    template_name = 'core/referral_detail.html'
    context_object_name = 'referral'


# Triage Views
class TriageListView(LoginRequiredMixin, ListView):
    model = Triage
    template_name = 'core/triage_list.html'
    context_object_name = 'triages'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Display items that need triage
        return queryset.filter(status=Triage.State.PENDING).order_by('-urgency', '-received_datetime')


class TriageDetailView(LoginRequiredMixin, DetailView):
    model = Triage
    template_name = 'core/triage_detail.html'
    context_object_name = 'triage'


# Visit Views
class VisitListView(LoginRequiredMixin, ListView):
    model = Visit
    template_name = 'core/visit_list.html'
    context_object_name = 'visits'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Show scheduled visits
        return queryset.filter(status=Visit.State.SCHEDULED).order_by('appointment_datetime')


class VisitDetailView(LoginRequiredMixin, DetailView):
    model = Visit
    template_name = 'core/visit_detail.html'
    context_object_name = 'visit'


# Report Views
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'core/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Show completed visits ready for reporting
        return queryset.filter(status=Report.State.COMPLETED).order_by('-study_completed_datetime')


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'core/report_detail.html'
    context_object_name = 'report'
