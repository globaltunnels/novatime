from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
import secrets
import requests

from .models import User, Session, AuditLog
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    MagicLinkRequestSerializer,
    OIDCTokenSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with session tracking."""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user from token
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = authenticate(
                request,
                username=request.data.get('email') or request.data.get('username'),
                password=request.data.get('password')
            )
            
            if user:
                # Create session record
                Session.objects.create(
                    user=user,
                    session_key=secrets.token_urlsafe(32),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    expires_at=timezone.now() + timezone.timedelta(days=1)
                )
                
                # Update last activity
                user.last_activity = timezone.now()
                user.save(update_fields=['last_activity'])
                
                # Log audit event
                AuditLog.objects.create(
                    user=user,
                    action='login',
                    resource_type='User',
                    resource_id=str(user.id),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'method': 'password'}
                )
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuthViewSet(GenericViewSet):
    """Authentication related views."""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """User registration."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Send email verification
            self.send_email_verification(user, request)
            
            # Log audit event
            AuditLog.objects.create(
                user=user,
                action='register',
                resource_type='User',
                resource_id=str(user.id),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'method': 'email'}
            )
            
            return Response({
                'message': 'Registration successful. Please check your email to verify your account.',
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_email(self, request):
        """Email verification."""
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                # Decode token to get user ID
                user_id = urlsafe_base64_decode(token).decode()
                user = get_object_or_404(User, id=user_id)
                
                if not user.is_email_verified:
                    user.is_email_verified = True
                    user.save()
                    
                    return Response({
                        'message': 'Email verified successfully.'
                    })
                else:
                    return Response({
                        'message': 'Email already verified.'
                    })
                    
            except Exception:
                return Response({
                    'error': 'Invalid verification token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def request_password_reset(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                self.send_password_reset_email(user, request)
            except User.DoesNotExist:
                pass  # Don't reveal if email exists
            
            return Response({
                'message': 'If the email exists, a password reset link has been sent.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """Reset password with token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Decode token
                user_id = urlsafe_base64_decode(token).decode()
                user = get_object_or_404(User, id=user_id)
                
                # Verify token is valid
                if default_token_generator.check_token(user, token):
                    user.set_password(new_password)
                    user.save()
                    
                    # Invalidate all sessions
                    Session.objects.filter(user=user).delete()
                    
                    return Response({
                        'message': 'Password reset successful.'
                    })
                else:
                    return Response({
                        'error': 'Invalid or expired token.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception:
                return Response({
                    'error': 'Invalid reset token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def magic_link(self, request):
        """Request magic link authentication."""
        serializer = MagicLinkRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                self.send_magic_link(user, request)
            except User.DoesNotExist:
                pass  # Don't reveal if email exists
            
            return Response({
                'message': 'If the email exists, a magic link has been sent.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def oidc_login(self, request):
        """OIDC/OAuth login."""
        serializer = OIDCTokenSerializer(data=request.data)
        if serializer.is_valid():
            provider = serializer.validated_data['provider']
            access_token = serializer.validated_data['access_token']
            
            # Verify token with provider and get user info
            user_info = self.verify_oidc_token(provider, access_token)
            
            if user_info:
                # Get or create user
                user, created = User.objects.get_or_create(
                    email=user_info['email'],
                    defaults={
                        'username': user_info['email'],
                        'first_name': user_info.get('first_name', ''),
                        'last_name': user_info.get('last_name', ''),
                        'is_email_verified': True,
                        'provider': provider,
                        'oidc_subject': user_info.get('sub', '')
                    }
                )
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Log audit event
                AuditLog.objects.create(
                    user=user,
                    action='login' if not created else 'register',
                    resource_type='User',
                    resource_id=str(user.id),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'method': 'oidc', 'provider': provider}
                )
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserProfileSerializer(user).data
                })
            else:
                return Response({
                    'error': 'Invalid token or provider error.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout user."""
        # Invalidate current session
        Session.objects.filter(user=request.user).delete()
        
        # Log audit event
        AuditLog.objects.create(
            user=request.user,
            action='logout',
            resource_type='User',
            resource_id=str(request.user.id),
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Logged out successfully'})
    
    def send_email_verification(self, user, request):
        """Send email verification email."""
        token = urlsafe_base64_encode(force_bytes(user.id))
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        send_mail(
            subject='Verify your NovaTime account',
            message=f'Click here to verify your email: {verification_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    
    def send_password_reset_email(self, user, request):
        """Send password reset email."""
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
        
        send_mail(
            subject='Reset your NovaTime password',
            message=f'Click here to reset your password: {reset_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    
    def send_magic_link(self, user, request):
        """Send magic link email."""
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        magic_url = f"{settings.FRONTEND_URL}/magic-login?uid={uid}&token={token}"
        
        send_mail(
            subject='Your NovaTime magic link',
            message=f'Click here to sign in: {magic_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    
    def verify_oidc_token(self, provider, access_token):
        """Verify OIDC token with provider."""
        try:
            if provider == 'google':
                response = requests.get(
                    f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}'
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'email': data.get('email'),
                        'first_name': data.get('given_name', ''),
                        'last_name': data.get('family_name', ''),
                        'sub': data.get('id')
                    }
            
            elif provider == 'github':
                response = requests.get(
                    'https://api.github.com/user',
                    headers={'Authorization': f'token {access_token}'}
                )
                if response.status_code == 200:
                    data = response.json()
                    # Get email from separate endpoint
                    email_response = requests.get(
                        'https://api.github.com/user/emails',
                        headers={'Authorization': f'token {access_token}'}
                    )
                    emails = email_response.json() if email_response.status_code == 200 else []
                    primary_email = next((e['email'] for e in emails if e['primary']), None)
                    
                    return {
                        'email': primary_email or data.get('email'),
                        'first_name': data.get('name', '').split(' ')[0] if data.get('name') else '',
                        'last_name': ' '.join(data.get('name', '').split(' ')[1:]) if data.get('name') else '',
                        'sub': str(data.get('id'))
                    }
            
            # Add more providers as needed
            
        except Exception as e:
            print(f"OIDC verification error: {e}")
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(APIView):
    """User profile management."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile."""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """Partially update user profile."""
        return self.put(request)


class ChangePasswordView(APIView):
    """Change password view."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Invalidate all sessions except current
            Session.objects.filter(user=user).delete()
            
            # Log audit event
            AuditLog.objects.create(
                user=user,
                action='password_change',
                resource_type='User',
                resource_id=str(user.id),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip