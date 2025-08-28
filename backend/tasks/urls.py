"""
URL configuration for tasks app.

This module defines URL patterns for the tasks API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet, TaskViewSet, AssignmentViewSet, EpicViewSet,
    SprintViewSet, DependencyViewSet, TemplateViewSet, CommentViewSet,
    AttachmentViewSet, TagViewSet, project_quality, ai_task_suggestions,
    optimize_assignments, project_predictive_analytics
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'epics', EpicViewSet, basename='epic')
router.register(r'sprints', SprintViewSet, basename='sprint')
router.register(r'dependencies', DependencyViewSet, basename='dependency')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path('projects/<uuid:project_id>/quality/', project_quality, name='project-quality'),
    path('projects/<uuid:project_id>/ai-suggestions/', ai_task_suggestions, name='ai-task-suggestions'),
    path('projects/<uuid:project_id>/optimize-assignments/', optimize_assignments, name='optimize-assignments'),
    path('projects/<uuid:project_id>/predictive-analytics/', project_predictive_analytics, name='project-predictive-analytics'),
]