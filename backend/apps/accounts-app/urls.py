"""
URL configuration for accounts app.

This module defines URL patterns for the accounts API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, UserProfileViewSet, UserSessionViewSet,
    PasswordResetTokenViewSet, EmailVerificationTokenViewSet,
    UserActivityViewSet, register, login, refresh_token,
    request_password_reset, confirm_password_reset, request_magic_link,
    verify_email, me, update_me, my_preferences, update_preferences,
    logout, feedback, notifications, mark_notifications_read
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'sessions', UserSessionViewSet, basename='session')
router.register(r'password-reset-tokens', PasswordResetTokenViewSet, basename='password-reset-token')
router.register(r'email-verification-tokens', EmailVerificationTokenViewSet, basename='email-verification-token')
router.register(r'activities', UserActivityViewSet, basename='activity')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Authentication endpoints
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    path('auth/refresh/', refresh_token, name='refresh-token'),
    path('auth/logout/', logout, name='logout'),
    path('auth/password/reset/', request_password_reset, name='request-password-reset'),
    path('auth/password/confirm/', confirm_password_reset, name='confirm-password-reset'),
    path('auth/magic-link/', request_magic_link, name='request-magic-link'),
    path('auth/verify-email/', verify_email, name='verify-email'),

    # Current user endpoints
    path('me/', me, name='me'),
    path('me/update/', update_me, name='update-me'),
    path('me/preferences/', my_preferences, name='my-preferences'),
    path('me/preferences/update/', update_preferences, name='update-preferences'),

    # User interaction endpoints
    path('feedback/', feedback, name='feedback'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/mark-read/', mark_notifications_read, name='mark-notifications-read'),
]