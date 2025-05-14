from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Patient URLs
    path('patients/', views.PatientListView.as_view(), name='patient_list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    
    # Referral URLs
    path('referrals/', views.ReferralListView.as_view(), name='referral_list'),
    path('referrals/<int:pk>/', views.ReferralDetailView.as_view(), name='referral_detail'),
    
    # Triage URLs
    path('triage/', views.TriageListView.as_view(), name='triage_list'),
    path('triage/<int:pk>/', views.TriageDetailView.as_view(), name='triage_detail'),
    
    # Visit URLs
    path('visits/', views.VisitListView.as_view(), name='visit_list'),
    path('visits/<int:pk>/', views.VisitDetailView.as_view(), name='visit_detail'),
    
    # Report URLs
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
]
