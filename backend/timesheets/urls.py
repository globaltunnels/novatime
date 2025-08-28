"""
URL configuration for timesheets app.

This module defines URL patterns for the timesheets API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TimesheetPeriodViewSet, TimesheetViewSet, TimesheetEntryViewSet,
    ApprovalWorkflowViewSet, TimesheetCommentViewSet, TimesheetTemplateViewSet,
    bulk_timesheet_action, timesheets_report, timesheets_summary,
    create_timesheet_from_template
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'timesheet-periods', TimesheetPeriodViewSet, basename='timesheet-period')
router.register(r'timesheets', TimesheetViewSet, basename='timesheet')
router.register(r'timesheet-entries', TimesheetEntryViewSet, basename='timesheet-entry')
router.register(r'approval-workflows', ApprovalWorkflowViewSet, basename='approval-workflow')
router.register(r'timesheet-comments', TimesheetCommentViewSet, basename='timesheet-comment')
router.register(r'timesheet-templates', TimesheetTemplateViewSet, basename='timesheet-template')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path('bulk-action/', bulk_timesheet_action, name='bulk-timesheet-action'),
    path('reports/', timesheets_report, name='timesheets-report'),
    path('summary/', timesheets_summary, name='timesheets-summary'),
    path('from-template/<uuid:template_id>/', create_timesheet_from_template, name='create-from-template'),
]