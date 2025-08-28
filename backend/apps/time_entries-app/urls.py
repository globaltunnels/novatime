"""
URL configuration for time_entries app.

This module defines URL patterns for the time entries API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TimeEntryViewSet, TimerViewSet, TimeEntryApprovalViewSet, IdlePeriodViewSet,
    TimeEntryTemplateViewSet, TimeEntryCategoryViewSet, TimeEntryTagViewSet,
    TimeEntryCommentViewSet, TimeEntryAttachmentViewSet, duplicate_time_entries,
    merge_time_entries, split_time_entry, lock_time_entries, unlock_time_entries,
    time_entry_audit, forecast_time_entries, analyze_productivity, check_compliance,
    backup_time_entries
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')
router.register(r'timers', TimerViewSet, basename='timer')
router.register(r'approvals', TimeEntryApprovalViewSet, basename='time-entry-approval')
router.register(r'idle-periods', IdlePeriodViewSet, basename='idle-period')
router.register(r'templates', TimeEntryTemplateViewSet, basename='time-entry-template')
router.register(r'categories', TimeEntryCategoryViewSet, basename='time-entry-category')
router.register(r'tags', TimeEntryTagViewSet, basename='time-entry-tag')
router.register(r'comments', TimeEntryCommentViewSet, basename='time-entry-comment')
router.register(r'attachments', TimeEntryAttachmentViewSet, basename='time-entry-attachment')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path('duplicate/', duplicate_time_entries, name='duplicate-time-entries'),
    path('merge/', merge_time_entries, name='merge-time-entries'),
    path('split/', split_time_entry, name='split-time-entry'),
    path('lock/', lock_time_entries, name='lock-time-entries'),
    path('unlock/', unlock_time_entries, name='unlock-time-entries'),
    path('audit/', time_entry_audit, name='time-entry-audit'),
    path('forecast/', forecast_time_entries, name='forecast-time-entries'),
    path('productivity/', analyze_productivity, name='analyze-productivity'),
    path('compliance/', check_compliance, name='check-compliance'),
    path('backup/', backup_time_entries, name='backup-time-entries'),
]