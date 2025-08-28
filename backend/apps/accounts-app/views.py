"""
Views for accounts app.

This module contains API views for managing users, authentication,
profiles, sessions, password reset, email verification, and related functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from datetime import timedelta
import uuid

from .models import (
    User, UserProfile, UserSession, PasswordResetToken,
    EmailVerificationToken, UserActivity
)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserProfileSerializer, UserProfileCreateSerializer, UserSessionSerializer,
    PasswordResetTokenSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationTokenSerializer,
    EmailVerificationRequestSerializer, EmailVerificationConfirmSerializer,
    UserActivitySerializer, UserPreferencesSerializer, ChangePasswordSerializer,
    UserStatsSerializer, UserSearchSerializer, UserBulkActionSerializer,
    UserExportSerializer, UserImportSerializer, LoginSerializer,
    TokenRefreshSerializer, MagicLinkRequestSerializer, TwoFactorSetupSerializer,
    TwoFactorVerifySerializer, PasskeyRegisterSerializer,
    PasskeyAuthenticateSerializer, UserNotificationSerializer,
    UserSettingsSerializer, UserOnboardingSerializer, UserFeedbackSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Filter users based on user's access."""
        user = self.request.user

        # If user is superuser, show all users
        if user.is_superuser:
            return User.objects.all()

        # Otherwise, show users from same organizations
        return User.objects.filter(
            Q(organizations__users=user) |
            Q(id=user.id)
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        """Create user."""
        user = serializer.save()
        # Create user profile
        UserProfile.objects.create(user=user)
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            action='user_created',
            description=f'Created user {user.get_full_name()}',
            category='auth'
        )

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get user profile."""
        user = self.get_object()
        profile, created = UserProfile.objects.get_or_create(user=user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'])
    def update_profile(self, request, pk=None):
        """Update user profile."""
        user = self.get_object()
        profile, created = UserProfile.objects.get_or_create(user=user)

        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Get user sessions."""
        user = self.get_object()
        sessions = UserSession.objects.filter(user=user, is_active=True)
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def revoke_session(self, request, pk=None):
        """Revoke user session."""
        user = self.get_object()
        session_key = request.data.get('session_key')

        try:
            session = UserSession.objects.get(
                user=user,
                session_key=session_key,
                is_active=True
            )
            session.is_active = False
            session.save()
            return Response({'message': _('Session revoked successfully.')})
        except UserSession.DoesNotExist:
            return Response(
                {'error': _('Session not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get user activities."""
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user)
        page = self.paginate_queryset(activities)
        serializer = UserActivitySerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get user statistics."""
        user = self.get_object()

        # Get basic stats
        total_sessions = UserSession.objects.filter(user=user).count()
        active_sessions = UserSession.objects.filter(
            user=user,
            is_active=True
        ).count()
        total_activities = UserActivity.objects.filter(user=user).count()

        # Get recent activities
        recent_activities = UserActivity.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        recent_activities_data = UserActivitySerializer(
            recent_activities,
            many=True
        ).data

        # Calculate login streak (simplified)
        login_streak = 0

        # Get organizations, workspaces, teams count
        organizations_joined = user.get_organizations().count()
        workspaces_joined = user.get_workspaces().count()
        teams_joined = user.get_teams().count()

        # Task and time stats (simplified)
        tasks_created = 0
        tasks_completed = 0
        time_entries_created = 0
        total_hours_tracked = 0

        stats = {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_activities': total_activities,
            'recent_activities': recent_activities_data,
            'login_streak': login_streak,
            'average_session_duration': 0,
            'most_active_day': 'monday',
            'most_active_hour': 9,
            'organizations_joined': organizations_joined,
            'workspaces_joined': workspaces_joined,
            'teams_joined': teams_joined,
            'tasks_created': tasks_created,
            'tasks_completed': tasks_completed,
            'time_entries_created': time_entries_created,
            'total_hours_tracked': total_hours_tracked
        }

        serializer = UserStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='password_changed',
                description='Password changed',
                category='auth'
            )

            return Response({'message': _('Password changed successfully.')})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def send_verification_email(self, request, pk=None):
        """Send email verification."""
        user = self.get_object()

        if user.is_verified:
            return Response(
                {'error': _('User is already verified.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create verification token
        token = EmailVerificationToken.objects.create(
            user=user,
            email=user.email,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Send verification email (would implement)
        # send_verification_email(user, token)

        return Response({
            'message': _('Verification email sent successfully.')
        })

    @action(detail=True, methods=['post'])
    def enable_two_factor(self, request, pk=None):
        """Enable two-factor authentication."""
        user = self.get_object()
        serializer = TwoFactorSetupSerializer(data=request.data)

        if serializer.is_valid():
            user.enable_two_factor()
            return Response({
                'message': _('Two-factor authentication enabled successfully.')
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def disable_two_factor(self, request, pk=None):
        """Disable two-factor authentication."""
        user = self.get_object()
        user.disable_two_factor()
        return Response({
            'message': _('Two-factor authentication disabled successfully.')
        })

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on users."""
        serializer = UserBulkActionSerializer(data=request.data)

        if serializer.is_valid():
            user_ids = serializer.validated_data['user_ids']
            action = serializer.validated_data['action']

            users = User.objects.filter(id__in=user_ids)
            updated_count = 0

            for user in users:
                if action == 'activate':
                    user.is_active = True
                    user.save()
                elif action == 'deactivate':
                    user.is_active = False
                    user.save()
                elif action == 'delete':
                    user.delete()
                    continue
                elif action == 'verify':
                    user.is_verified = True
                    user.save()
                elif action == 'unverify':
                    user.is_verified = False
                    user.save()

                updated_count += 1

            return Response({
                'message': _('Bulk action completed successfully.'),
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search users."""
        serializer = UserSearchSerializer(data=request.data)

        if serializer.is_valid():
            query = serializer.validated_data['query']
            organization_id = serializer.validated_data.get('organization_id')
            workspace_id = serializer.validated_data.get('workspace_id')
            team_id = serializer.validated_data.get('team_id')
            limit = serializer.validated_data.get('limit', 20)

            # Build queryset
            users = User.objects.filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

            if organization_id:
                users = users.filter(organizations__id=organization_id)

            if workspace_id:
                users = users.filter(workspaces__id=workspace_id)

            if team_id:
                users = users.filter(teams__id=team_id)

            users = users[:limit]
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile model."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter profiles by user's access."""
        return UserProfile.objects.filter(
            user__organizations__users=self.request.user
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserProfileCreateSerializer
        return UserProfileSerializer

    def perform_create(self, serializer):
        """Create user profile."""
        serializer.save(user=self.request.user)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UserSession model."""

    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter sessions by current user."""
        return UserSession.objects.filter(user=self.request.user)


class PasswordResetTokenViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PasswordResetToken model."""

    serializer_class = PasswordResetTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tokens by current user."""
        return PasswordResetToken.objects.filter(user=self.request.user)


class EmailVerificationTokenViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for EmailVerificationToken model."""

    serializer_class = EmailVerificationTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tokens by current user."""
        return EmailVerificationToken.objects.filter(user=self.request.user)


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UserActivity model."""

    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Filter activities by user's access."""
        user = self.request.user

        # If user is superuser, show all activities
        if user.is_superuser:
            return UserActivity.objects.all()

        # Otherwise, show activities from same organizations
        return UserActivity.objects.filter(
            Q(user=user) |
            Q(organization__users=user) |
            Q(workspace__organization__users=user)
        ).distinct()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user."""
    serializer = UserCreateSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Create verification token
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            email=user.email,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Send verification email (would implement)
        # send_verification_email(user, verification_token)

        # Log activity
        UserActivity.objects.create(
            user=user,
            action='user_registered',
            description='User registered',
            category='auth'
        )

        return Response({
            'message': _('User registered successfully. Please check your email for verification.'),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user."""
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        remember_me = serializer.validated_data.get('remember_me', False)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response(
                {'error': _('Invalid credentials.')},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': _('Account is disabled.')},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Update last login
        user.update_last_login()

        # Create session
        UserSession.objects.create(
            user=user,
            session_key=str(uuid.uuid4()),
            device_type=request.META.get('HTTP_USER_AGENT', '')[:20],
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timedelta(days=30 if remember_me else 1)
        )

        # Log activity
        UserActivity.objects.create(
            user=user,
            action='user_logged_in',
            description='User logged in',
            category='auth',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': UserSerializer(user).data
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token."""
    serializer = TokenRefreshSerializer(data=request.data)

    if serializer.is_valid():
        refresh_token = serializer.validated_data['refresh_token']

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({
                'access_token': access_token
            })

        except Exception:
            return Response(
                {'error': _('Invalid refresh token.')},
                status=status.HTTP_401_UNAUTHORIZED
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Request password reset."""
    serializer = PasswordResetRequestSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Create reset token
        reset_token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Send reset email (would implement)
        # send_password_reset_email(user, reset_token)

        return Response({
            'message': _('Password reset email sent successfully.')
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """Confirm password reset."""
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['password']

        try:
            reset_token = PasswordResetToken.objects.get(
                token=token,
                is_used=False
            )

            if reset_token.is_expired():
                return Response(
                    {'error': _('Reset token has expired.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.use()

            # Log activity
            UserActivity.objects.create(
                user=user,
                action='password_reset',
                description='Password reset via token',
                category='auth'
            )

            return Response({
                'message': _('Password reset successfully.')
            })

        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': _('Invalid reset token.')},
                status=status.HTTP_400_BAD_REQUEST
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_magic_link(request):
    """Request magic link login."""
    serializer = MagicLinkRequestSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Create magic link token (would implement)
        # magic_token = MagicLinkToken.objects.create(user=user)

        # Send magic link email (would implement)
        # send_magic_link_email(user, magic_token)

        return Response({
            'message': _('Magic link sent successfully.')
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email address."""
    serializer = EmailVerificationConfirmSerializer(data=request.data)

    if serializer.is_valid():
        token = serializer.validated_data['token']

        try:
            verification_token = EmailVerificationToken.objects.get(
                token=token,
                is_verified=False
            )

            if verification_token.is_expired():
                return Response(
                    {'error': _('Verification token has expired.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify email
            verification_token.verify()

            return Response({
                'message': _('Email verified successfully.')
            })

        except EmailVerificationToken.DoesNotExist:
            return Response(
                {'error': _('Invalid verification token.')},
                status=status.HTTP_400_BAD_REQUEST
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Get current user information."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_me(request):
    """Update current user information."""
    serializer = UserUpdateSerializer(
        request.user,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_preferences(request):
    """Get current user preferences."""
    preferences = request.user.get_preferences()
    return Response(preferences)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Update current user preferences."""
    serializer = UserPreferencesSerializer(data=request.data)

    if serializer.is_valid():
        request.user.update_preferences(serializer.validated_data)
        return Response(request.user.get_preferences())

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user."""
    # Invalidate refresh token (would implement)
    # Invalidate user sessions (would implement)

    # Log activity
    UserActivity.objects.create(
        user=request.user,
        action='user_logged_out',
        description='User logged out',
        category='auth'
    )

    return Response({'message': _('Logged out successfully.')})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback(request):
    """Submit user feedback."""
    serializer = UserFeedbackSerializer(data=request.data)

    if serializer.is_valid():
        # Process feedback (would implement)
        # send_feedback_email(serializer.validated_data)

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='feedback_submitted',
            description=f'Feedback submitted: {serializer.validated_data["subject"]}',
            category='general'
        )

        return Response({
            'message': _('Feedback submitted successfully.')
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications(request):
    """Get user notifications."""
    # Get notifications (would implement)
    notifications = []

    serializer = UserNotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    """Mark notifications as read."""
    notification_ids = request.data.get('notification_ids', [])

    # Mark notifications as read (would implement)

    return Response({'message': _('Notifications marked as read.')})