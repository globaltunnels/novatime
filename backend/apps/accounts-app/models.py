"""
Accounts models for NovaTime.

This app handles user management, authentication, profiles, and account-related functionality.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """Custom user manager for NovaTime users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for NovaTime.

    Extends Django's AbstractUser with additional fields specific to NovaTime.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Override username field - we'll use email as username
    username = None
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. A valid email address.')
    )

    # Basic information
    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=True,
        help_text=_('User\'s first name')
    )

    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=True,
        help_text=_('User\'s last name')
    )

    # Profile information
    avatar_url = models.URLField(
        _('avatar URL'),
        blank=True,
        help_text=_('Profile picture URL')
    )

    bio = models.TextField(
        _('bio'),
        blank=True,
        max_length=500,
        help_text=_('Short bio or description')
    )

    title = models.CharField(
        _('job title'),
        max_length=100,
        blank=True,
        help_text=_('Current job title')
    )

    department = models.CharField(
        _('department'),
        max_length=100,
        blank=True,
        help_text=_('Department or team')
    )

    # Contact information
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4,6}$',
            message=_('Enter a valid phone number.')
        )],
        help_text=_('Phone number')
    )

    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='UTC',
        help_text=_('User\'s timezone')
    )

    language = models.CharField(
        _('language'),
        max_length=10,
        default='en',
        help_text=_('Preferred language (ISO 639-1 code)')
    )

    # Work preferences
    work_hours_start = models.TimeField(
        _('work hours start'),
        default='09:00:00',
        help_text=_('Preferred work start time')
    )

    work_hours_end = models.TimeField(
        _('work hours end'),
        default='17:00:00',
        help_text=_('Preferred work end time')
    )

    work_days = models.JSONField(
        _('work days'),
        default=list,  # ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        blank=True,
        help_text=_('Days of the week the user works')
    )

    # Notification preferences
    email_notifications = models.BooleanField(
        _('email notifications'),
        default=True,
        help_text=_('Receive email notifications')
    )

    push_notifications = models.BooleanField(
        _('push notifications'),
        default=True,
        help_text=_('Receive push notifications')
    )

    weekly_digest = models.BooleanField(
        _('weekly digest'),
        default=True,
        help_text=_('Receive weekly digest emails')
    )

    # Privacy settings
    profile_visibility = models.CharField(
        _('profile visibility'),
        max_length=20,
        default='team',
        choices=[
            ('public', 'Public'),
            ('organization', 'Organization members'),
            ('team', 'Team members'),
            ('private', 'Private'),
        ],
        help_text=_('Who can see your profile')
    )

    show_online_status = models.BooleanField(
        _('show online status'),
        default=True,
        help_text=_('Show when you are online')
    )

    # Security settings
    two_factor_enabled = models.BooleanField(
        _('two-factor authentication'),
        default=False,
        help_text=_('Two-factor authentication enabled')
    )

    passkeys_enabled = models.BooleanField(
        _('passkeys enabled'),
        default=False,
        help_text=_('Passkeys/WebAuthn enabled')
    )

    # Account status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )

    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Email address has been verified')
    )

    # Subscription and billing
    stripe_customer_id = models.CharField(
        _('Stripe customer ID'),
        max_length=100,
        blank=True,
        help_text=_('Stripe customer identifier')
    )

    # Integration settings
    calendar_integration = models.JSONField(
        _('calendar integration'),
        default=dict,
        blank=True,
        help_text=_('Calendar integration settings')
    )

    slack_integration = models.JSONField(
        _('Slack integration'),
        default=dict,
        blank=True,
        help_text=_('Slack integration settings')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(
        _('last login'),
        null=True,
        blank=True,
        help_text=_('Last login timestamp')
    )
    last_activity_at = models.DateTimeField(
        _('last activity'),
        null=True,
        blank=True,
        help_text=_('Last activity timestamp')
    )

    # Manager fields
    objects = UserManager()

    # Set email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ['email']
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_login_at']),
            models.Index(fields=['last_activity_at']),
        ]

    def __str__(self):
        """Return string representation of user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]

    def save(self, *args, **kwargs):
        """Save user and handle related updates."""
        # Set default work days if not set
        if not self.work_days:
            self.work_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

        super().save(*args, **kwargs)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at'])

    def update_last_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])

    def is_online(self):
        """Check if user is currently online."""
        if not self.last_activity_at:
            return False

        # Consider online if activity within last 5 minutes
        return (timezone.now() - self.last_activity_at).seconds < 300

    def get_profile_completion_percentage(self):
        """Calculate profile completion percentage."""
        fields = [
            self.first_name, self.last_name, self.bio, self.title,
            self.avatar_url, self.phone, self.timezone
        ]

        completed_fields = sum(1 for field in fields if field)
        return int((completed_fields / len(fields)) * 100)

    def can_access_organization(self, organization):
        """Check if user can access an organization."""
        return self.organization_memberships.filter(
            organization=organization,
            is_active=True
        ).exists()

    def can_access_workspace(self, workspace):
        """Check if user can access a workspace."""
        return self.workspace_memberships.filter(
            workspace=workspace,
            is_active=True
        ).exists()

    def get_organizations(self):
        """Get user's organizations."""
        return self.organizations.filter(
            memberships__user=self,
            memberships__is_active=True
        ).distinct()

    def get_workspaces(self):
        """Get user's workspaces."""
        return self.workspaces.filter(
            memberships__user=self,
            memberships__is_active=True
        ).distinct()

    def get_teams(self):
        """Get user's teams."""
        return self.teams.filter(
            memberships__user=self,
            memberships__is_active=True
        ).distinct()

    def get_primary_organization(self):
        """Get user's primary organization."""
        membership = self.organization_memberships.filter(
            is_active=True
        ).first()

        return membership.organization if membership else None

    def send_verification_email(self):
        """Send email verification."""
        # Implementation would go here
        pass

    def enable_two_factor(self):
        """Enable two-factor authentication."""
        self.two_factor_enabled = True
        self.save(update_fields=['two_factor_enabled'])

    def disable_two_factor(self):
        """Disable two-factor authentication."""
        self.two_factor_enabled = False
        self.save(update_fields=['two_factor_enabled'])

    def get_preferences(self):
        """Get user preferences as dictionary."""
        return {
            'timezone': self.timezone,
            'language': self.language,
            'work_hours_start': self.work_hours_start.isoformat(),
            'work_hours_end': self.work_hours_end.isoformat(),
            'work_days': self.work_days,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'weekly_digest': self.weekly_digest,
            'profile_visibility': self.profile_visibility,
            'show_online_status': self.show_online_status,
        }

    def update_preferences(self, preferences):
        """Update user preferences."""
        for key, value in preferences.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.save()


class UserProfile(models.Model):
    """
    Extended user profile model.

    Contains additional user information and preferences.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text=_('User this profile belongs to')
    )

    # Personal information
    date_of_birth = models.DateField(
        _('date of birth'),
        null=True,
        blank=True,
        help_text=_('User\'s date of birth')
    )

    gender = models.CharField(
        _('gender'),
        max_length=20,
        blank=True,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('non-binary', 'Non-binary'),
            ('prefer-not-to-say', 'Prefer not to say'),
            ('other', 'Other'),
        ],
        help_text=_('User\'s gender')
    )

    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        help_text=_('City and country')
    )

    # Professional information
    years_of_experience = models.PositiveIntegerField(
        _('years of experience'),
        null=True,
        blank=True,
        help_text=_('Years of professional experience')
    )

    skills = models.JSONField(
        _('skills'),
        default=list,
        blank=True,
        help_text=_('List of user skills')
    )

    certifications = models.JSONField(
        _('certifications'),
        default=list,
        blank=True,
        help_text=_('List of certifications')
    )

    # Social links
    linkedin_url = models.URLField(
        _('LinkedIn URL'),
        blank=True,
        help_text=_('LinkedIn profile URL')
    )

    github_url = models.URLField(
        _('GitHub URL'),
        blank=True,
        help_text=_('GitHub profile URL')
    )

    twitter_handle = models.CharField(
        _('Twitter handle'),
        max_length=50,
        blank=True,
        help_text=_('Twitter handle (without @)')
    )

    website_url = models.URLField(
        _('personal website'),
        blank=True,
        help_text=_('Personal website URL')
    )

    # Preferences
    theme = models.CharField(
        _('theme'),
        max_length=20,
        default='system',
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('system', 'System'),
        ],
        help_text=_('Preferred theme')
    )

    date_format = models.CharField(
        _('date format'),
        max_length=20,
        default='MM/DD/YYYY',
        help_text=_('Preferred date format')
    )

    time_format = models.CharField(
        _('time format'),
        max_length=20,
        default='12h',
        choices=[
            ('12h', '12-hour'),
            ('24h', '24-hour'),
        ],
        help_text=_('Preferred time format')
    )

    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('Preferred currency')
    )

    # Work preferences
    work_style = models.CharField(
        _('work style'),
        max_length=20,
        default='hybrid',
        choices=[
            ('remote', 'Remote'),
            ('office', 'Office'),
            ('hybrid', 'Hybrid'),
        ],
        help_text=_('Preferred work style')
    )

    meeting_availability = models.JSONField(
        _('meeting availability'),
        default=dict,
        blank=True,
        help_text=_('Meeting availability preferences')
    )

    # Notification settings
    notification_preferences = models.JSONField(
        _('notification preferences'),
        default=dict,
        blank=True,
        help_text=_('Detailed notification preferences')
    )

    # Privacy settings
    data_sharing = models.BooleanField(
        _('data sharing'),
        default=True,
        help_text=_('Allow data sharing for analytics')
    )

    marketing_emails = models.BooleanField(
        _('marketing emails'),
        default=False,
        help_text=_('Receive marketing emails')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user']
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"

    def get_completion_percentage(self):
        """Calculate profile completion percentage."""
        fields = [
            self.date_of_birth, self.location, self.years_of_experience,
            self.linkedin_url, self.github_url, self.website_url
        ]

        completed_fields = sum(1 for field in fields if field)
        return int((completed_fields / len(fields)) * 100)


class UserSession(models.Model):
    """
    User session model for tracking user sessions and devices.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        help_text=_('User this session belongs to')
    )

    # Session information
    session_key = models.CharField(
        _('session key'),
        max_length=100,
        unique=True,
        help_text=_('Django session key')
    )

    device_type = models.CharField(
        _('device type'),
        max_length=20,
        blank=True,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
        ],
        help_text=_('Type of device')
    )

    device_name = models.CharField(
        _('device name'),
        max_length=100,
        blank=True,
        help_text=_('Device name or model')
    )

    browser = models.CharField(
        _('browser'),
        max_length=50,
        blank=True,
        help_text=_('Browser name')
    )

    ip_address = models.GenericIPAddressField(
        _('IP address'),
        blank=True,
        null=True,
        help_text=_('IP address of the session')
    )

    user_agent = models.TextField(
        _('user agent'),
        blank=True,
        help_text=_('Browser user agent string')
    )

    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        help_text=_('Approximate location based on IP')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the session is active')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(
        _('last activity'),
        default=timezone.now,
        help_text=_('Last activity in this session')
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('When the session expires')
    )

    class Meta:
        ordering = ['-last_activity_at']
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_activity_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Session for {self.user.get_full_name()} ({self.device_type})"

    def is_expired(self):
        """Check if session is expired."""
        return timezone.now() > self.expires_at

    def extend(self, hours=24):
        """Extend session expiration."""
        self.expires_at = timezone.now() + timezone.timedelta(hours=hours)
        self.save(update_fields=['expires_at'])

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])


class PasswordResetToken(models.Model):
    """
    Password reset token model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        help_text=_('User requesting password reset')
    )

    # Token
    token = models.CharField(
        _('token'),
        max_length=100,
        unique=True,
        help_text=_('Reset token')
    )

    # Status
    is_used = models.BooleanField(
        _('used'),
        default=False,
        help_text=_('Whether the token has been used')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('When the token expires')
    )
    used_at = models.DateTimeField(
        _('used at'),
        null=True,
        blank=True,
        help_text=_('When the token was used')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['token']),
            models.Index(fields=['is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Password reset for {self.user.get_full_name()}"

    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at

    def use(self):
        """Mark token as used."""
        if not self.is_used and not self.is_expired():
            self.is_used = True
            self.used_at = timezone.now()
            self.save(update_fields=['is_used', 'used_at'])
            return True
        return False


class EmailVerificationToken(models.Model):
    """
    Email verification token model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification_tokens',
        help_text=_('User to verify email for')
    )

    # Token
    token = models.CharField(
        _('token'),
        max_length=100,
        unique=True,
        help_text=_('Verification token')
    )

    # Email
    email = models.EmailField(
        _('email'),
        help_text=_('Email address to verify')
    )

    # Status
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether the email has been verified')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('When the token expires')
    )
    verified_at = models.DateTimeField(
        _('verified at'),
        null=True,
        blank=True,
        help_text=_('When the email was verified')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('email verification token')
        verbose_name_plural = _('email verification tokens')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Email verification for {self.email}"

    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at

    def verify(self):
        """Mark email as verified."""
        if not self.is_verified and not self.is_expired():
            self.is_verified = True
            self.verified_at = timezone.now()
            self.user.is_verified = True
            self.user.save(update_fields=['is_verified'])
            self.save(update_fields=['is_verified', 'verified_at'])
            return True
        return False


class UserActivity(models.Model):
    """
    User activity log model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        help_text=_('User who performed the activity')
    )

    # Activity information
    action = models.CharField(
        _('action'),
        max_length=100,
        help_text=_('Action performed')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the activity')
    )

    category = models.CharField(
        _('category'),
        max_length=50,
        choices=[
            ('auth', 'Authentication'),
            ('profile', 'Profile'),
            ('organization', 'Organization'),
            ('workspace', 'Workspace'),
            ('project', 'Project'),
            ('task', 'Task'),
            ('time', 'Time Tracking'),
            ('settings', 'Settings'),
        ],
        help_text=_('Category of the activity')
    )

    # Context
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        blank=True,
        null=True,
        help_text=_('IP address of the user')
    )

    user_agent = models.TextField(
        _('user agent'),
        blank=True,
        help_text=_('Browser user agent')
    )

    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the activity')
    )

    # Organization context
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text=_('Organization context')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text=_('Workspace context')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['category']),
            models.Index(fields=['organization']),
            models.Index(fields=['workspace']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()}: {self.action} ({self.created_at})"


# Add reverse relationships
User.add_to_class(
    'organizations',
    models.ManyToManyField(
        'organizations.Organization',
        through='organizations.OrganizationMembership',
        related_name='users',
        help_text=_('Organizations this user belongs to')
    )
)

User.add_to_class(
    'workspaces',
    models.ManyToManyField(
        'organizations.Workspace',
        through='organizations.WorkspaceMembership',
        related_name='users',
        help_text=_('Workspaces this user belongs to')
    )
)

User.add_to_class(
    'teams',
    models.ManyToManyField(
        'organizations.Team',
        through='organizations.TeamMembership',
        related_name='users',
        help_text=_('Teams this user belongs to')
    )
)