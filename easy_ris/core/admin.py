from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.sections import TableSection, TemplateSection

from easy_ris.core.models import Patient, Request


@admin.register(Patient)
class PatientModelAdmin(ModelAdmin):
    pass


@admin.register(Request)
class RequestModelAdmin(ModelAdmin):
    pass
