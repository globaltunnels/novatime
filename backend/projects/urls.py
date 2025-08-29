from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet,
    ProjectViewSet,
    ProjectMemberViewSet,
    ProjectReportViewSet
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'members', ProjectMemberViewSet, basename='project-members')
router.register(r'reports', ProjectReportViewSet, basename='project-reports')

urlpatterns = [
    path('', include(router.urls)),
]