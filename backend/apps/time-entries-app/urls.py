"""
URL configuration for time entries app.

This module defines URL patterns for the time entries API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TimeEntryViewSet, TimerViewSet, IdlePeriodViewSet,
    TimeEntryTemplateViewSet, TimeEntryCommentViewSet,
    bulk_time_entry_action, time_entries_report,
    time_tracking_stats, timer_stats
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')
router.register(r'timers', TimerViewSet, basename='timer')
router.register(r'idle-periods', IdlePeriodViewSet, basename='idle-period')
router.register(r'time-entry-templates', TimeEntryTemplateViewSet, basename='time-entry-template')
router.register(r'time-entry-comments', TimeEntryCommentViewSet, basename='time-entry-comment')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path('bulk-action/', bulk_time_entry_action, name='bulk-time-entry-action'),
    path('reports/', time_entries_report, name='time-entries-report'),
    path('stats/tracking/', time_tracking_stats, name='time-tracking-stats'),
    path('stats/timer/', timer_stats, name='timer-stats'),
]