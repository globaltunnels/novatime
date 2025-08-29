from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Role


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 
                 'password', 'password_confirm', 'phone_number', 'user_timezone')
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user data."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['user_timezone'] = user.user_timezone
        
        return token


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                 'phone_number', 'avatar_url', 'user_timezone', 'is_email_verified',
                 'preferred_language', 'theme_preference', 'last_activity',
                 'date_joined', 'last_login')
        read_only_fields = ('id', 'email', 'date_joined', 'last_login', 'is_email_verified')


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for roles."""
    
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions', 'is_system_role',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    token = serializers.CharField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class MagicLinkRequestSerializer(serializers.Serializer):
    """Serializer for magic link authentication request."""
    email = serializers.EmailField(required=True)


class OIDCTokenSerializer(serializers.Serializer):
    """Serializer for OIDC token exchange."""
    provider = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)
    
    def validate_provider(self, value):
        allowed_providers = ['google', 'github', 'microsoft', 'apple']
        if value not in allowed_providers:
            raise serializers.ValidationError(f"Provider must be one of: {allowed_providers}")
        return value