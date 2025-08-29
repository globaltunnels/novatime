from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, UserRole, Session, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = ('email', 'username', 'first_name', 'last_name', 
                   'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 
                  'provider', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 
                                       'avatar_url', 'user_timezone')}),
        (_('Authentication'), {'fields': ('provider', 'oidc_subject', 'is_email_verified')}),
        (_('Preferences'), {'fields': ('preferred_language', 'theme_preference')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                     'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_activity')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'last_activity')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    
    list_display = ('name', 'description', 'is_system_role', 'created_at')
    list_filter = ('is_system_role', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_system_role')}),
        (_('Permissions'), {'fields': ('permissions',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for UserRole model."""
    
    list_display = ('user', 'role', 'organization', 'granted_by', 'granted_at')
    list_filter = ('role', 'granted_at')
    search_fields = ('user__email', 'user__username', 'role__name')
    readonly_fields = ('granted_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'role', 'organization')}),
        (_('Grant info'), {'fields': ('granted_by', 'granted_at')}),
    )


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin interface for Session model."""
    
    list_display = ('user', 'ip_address', 'location', 'is_active', 
                   'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'location')
    readonly_fields = ('created_at', 'last_accessed')
    
    fieldsets = (
        (None, {'fields': ('user', 'session_key', 'is_active')}),
        (_('Connection info'), {'fields': ('ip_address', 'user_agent', 'location')}),
        (_('Timestamps'), {'fields': ('created_at', 'last_accessed', 'expires_at')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""
    
    list_display = ('user', 'action', 'resource_type', 'resource_id', 
                   'organization', 'timestamp')
    list_filter = ('action', 'resource_type', 'timestamp')
    search_fields = ('user__email', 'user__username', 'action', 'resource_type', 
                    'resource_id')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        (None, {'fields': ('user', 'action', 'resource_type', 'resource_id')}),
        (_('Context'), {'fields': ('organization', 'ip_address', 'user_agent')}),
        (_('Details'), {'fields': ('details', 'timestamp')}),
    )
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted
