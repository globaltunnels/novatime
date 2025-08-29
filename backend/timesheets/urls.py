from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TimesheetViewSet,
    TimesheetEntryViewSet,
    TimesheetTemplateViewSet,
    TimesheetReportViewSet
)

router = DefaultRouter()
router.register(r'timesheets', TimesheetViewSet, basename='timesheets')
router.register(r'entries', TimesheetEntryViewSet, basename='timesheet-entries')
router.register(r'templates', TimesheetTemplateViewSet, basename='timesheet-templates')
router.register(r'reports', TimesheetReportViewSet, basename='timesheet-reports')

urlpatterns = [
    path('', include(router.urls)),
]