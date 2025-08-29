from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIModelViewSet,
    AIJobViewSet,
    SmartTimesheetSuggestionViewSet,
    TaskAssignmentRecommendationViewSet,
    AIInsightViewSet
)

router = DefaultRouter()
router.register(r'models', AIModelViewSet, basename='ai-models')
router.register(r'jobs', AIJobViewSet, basename='ai-jobs')
router.register(r'timesheet-suggestions', SmartTimesheetSuggestionViewSet, basename='timesheet-suggestions')
router.register(r'task-assignments', TaskAssignmentRecommendationViewSet, basename='task-assignments')
router.register(r'insights', AIInsightViewSet, basename='ai-insights')

urlpatterns = [
    path('', include(router.urls)),
]