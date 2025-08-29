from rest_framework import serializers
from django.utils import timezone
from django.db import models
from decimal import Decimal
from .models import Client, Project, ProjectMember, Epic
from iam.models import User


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for client management."""
    
    projects_count = serializers.SerializerMethodField()
    total_project_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'default_hourly_rate', 'currency', 'notes', 'is_active',
            'projects_count', 'total_project_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'projects_count', 'total_project_value', 'created_at', 'updated_at']
    
    def get_projects_count(self, obj):
        """Get number of projects for this client."""
        return obj.projects.filter(status__in=['planning', 'active', 'on_hold']).count()
    
    def get_total_project_value(self, obj):
        """Get total value of all client projects."""
        total = obj.projects.aggregate(
            total=models.Sum('fixed_price')
        )['total'] or Decimal('0.00')
        return total


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for project team members."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_avatar = serializers.CharField(source='user.avatar_url', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = [
            'id', 'user', 'user_name', 'user_email', 'user_avatar',
            'role', 'hourly_rate', 'allocation_percent', 'joined_at'
        ]
        read_only_fields = ['id', 'user_name', 'user_email', 'user_avatar', 'joined_at']
    
    def validate_allocation_percent(self, value):
        """Validate allocation percentage."""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Allocation must be between 1 and 100 percent")
        return value


class ProjectSerializer(serializers.ModelSerializer):
    """Main project serializer with comprehensive project information."""
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    
    members = ProjectMemberSerializer(many=True, read_only=True)
    
    # Calculated fields
    total_hours = serializers.SerializerMethodField()
    billable_hours = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()
    team_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'color', 'status',
            'start_date', 'end_date', 'billing_type', 'hourly_rate', 'fixed_price', 'budget_hours',
            'require_time_entry_notes', 'track_expenses', 'is_template', 'template_name',
            'client', 'client_name', 'manager', 'manager_name', 'workspace', 'workspace_name',
            'members', 'total_hours', 'billable_hours', 'total_cost',
            'progress_percentage', 'is_overdue', 'is_over_budget', 'team_size',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'client_name', 'manager_name', 'workspace_name',
            'members', 'total_hours', 'billable_hours', 'total_cost',
            'progress_percentage', 'is_overdue', 'is_over_budget', 'team_size',
            'created_at', 'updated_at'
        ]
    
    def get_total_hours(self, obj):
        """Calculate total hours tracked on this project."""
        from time_entries.models import TimeEntry
        total_minutes = TimeEntry.objects.filter(
            project=obj,
            duration_minutes__isnull=False
        ).aggregate(total=models.Sum('duration_minutes'))['total'] or 0
        return round(total_minutes / 60, 2)
    
    def get_billable_hours(self, obj):
        """Calculate billable hours tracked on this project."""
        from time_entries.models import TimeEntry
        total_minutes = TimeEntry.objects.filter(
            project=obj,
            is_billable=True,
            duration_minutes__isnull=False
        ).aggregate(total=models.Sum('duration_minutes'))['total'] or 0
        return round(total_minutes / 60, 2)
    
    def get_total_cost(self, obj):
        """Calculate total project cost based on time entries."""
        from time_entries.models import TimeEntry
        total_cost = Decimal('0.00')
        
        time_entries = TimeEntry.objects.filter(
            project=obj,
            duration_minutes__isnull=False
        ).select_related('user')
        
        for entry in time_entries:
            hours = Decimal(str(entry.duration_minutes / 60))
            rate = entry.hourly_rate or obj.hourly_rate or Decimal('0.00')
            total_cost += hours * rate
        
        return total_cost
    
    def get_progress_percentage(self, obj):
        """Calculate project progress based on task completion."""
        from tasks.models import Task
        tasks = Task.objects.filter(project=obj)
        total_tasks = tasks.count()
        
        if total_tasks == 0:
            return 0
        
        completed_tasks = tasks.filter(status='completed').count()
        return round((completed_tasks / total_tasks) * 100, 1)
    
    def get_is_overdue(self, obj):
        """Check if project is overdue."""
        if not obj.end_date:
            return False
        return timezone.now().date() > obj.end_date and obj.status != 'completed'
    
    def get_is_over_budget(self, obj):
        """Check if project is over budget hours."""
        if not obj.budget_hours:
            return False
        total_hours = self.get_total_hours(obj)
        return total_hours > float(obj.budget_hours)
    
    def get_team_size(self, obj):
        """Get number of team members."""
        return obj.members.count()
    
    def validate(self, data):
        """Validate project data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        billing_type = data.get('billing_type')
        if billing_type == 'hourly' and not data.get('hourly_rate'):
            raise serializers.ValidationError("Hourly rate is required for hourly billing")
        
        if billing_type == 'fixed' and not data.get('fixed_price'):
            raise serializers.ValidationError("Fixed price is required for fixed price billing")
        
        return data


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for project creation."""
    
    # Optional members to add during creation
    initial_members = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'color', 'status',
            'start_date', 'end_date', 'billing_type', 'hourly_rate', 'fixed_price', 'budget_hours',
            'client', 'manager', 'require_time_entry_notes', 'track_expenses',
            'initial_members'
        ]
    
    def create(self, validated_data):
        """Create project with initial team members."""
        initial_members = validated_data.pop('initial_members', [])
        project = super().create(validated_data)
        
        # Add initial team members
        for user_id in initial_members:
            try:
                user = User.objects.get(id=user_id)
                ProjectMember.objects.create(
                    project=project,
                    user=user,
                    role='member'
                )
            except User.DoesNotExist:
                continue
        
        return project


class ProjectSummarySerializer(serializers.ModelSerializer):
    """Lightweight project serializer for lists and references."""
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    total_hours = serializers.SerializerMethodField()
    team_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'color', 'status', 'billing_type',
            'start_date', 'end_date', 'client_name', 'manager_name',
            'total_hours', 'team_size'
        ]
    
    def get_total_hours(self, obj):
        """Calculate total hours tracked on this project."""
        from time_entries.models import TimeEntry
        total_minutes = TimeEntry.objects.filter(
            project=obj,
            duration_minutes__isnull=False
        ).aggregate(total=models.Sum('duration_minutes'))['total'] or 0
        return round(total_minutes / 60, 2)
    
    def get_team_size(self, obj):
        """Get number of team members."""
        return obj.members.count()


class ProjectTimelineSerializer(serializers.Serializer):
    """Serializer for project timeline view."""
    
    project = ProjectSummarySerializer(read_only=True)
    milestones = serializers.SerializerMethodField()
    tasks_by_week = serializers.SerializerMethodField()
    team_utilization = serializers.SerializerMethodField()
    
    def get_milestones(self, obj):
        """Get project milestones."""
        # This would be implemented when milestone models are added
        return []
    
    def get_tasks_by_week(self, obj):
        """Get tasks grouped by week."""
        from tasks.models import Task
        from datetime import timedelta
        import calendar
        
        if not obj.start_date or not obj.end_date:
            return []
        
        tasks = Task.objects.filter(project=obj).order_by('due_date')
        weeks = []
        
        current_date = obj.start_date
        while current_date <= obj.end_date:
            week_end = current_date + timedelta(days=6)
            week_tasks = tasks.filter(
                due_date__range=[current_date, week_end]
            ).values('id', 'title', 'status', 'due_date')
            
            weeks.append({
                'start_date': current_date,
                'end_date': min(week_end, obj.end_date),
                'tasks': list(week_tasks)
            })
            
            current_date = week_end + timedelta(days=1)
        
        return weeks
    
    def get_team_utilization(self, obj):
        """Get team utilization for the project."""
        utilization = []
        
        for member in obj.members.all():
            # This would calculate actual utilization based on time entries
            utilization.append({
                'user_id': str(member.user.id),
                'user_name': member.user.get_full_name(),
                'role': member.role,
                'allocation_percent': member.allocation_percent,
                'actual_hours_this_week': 0,  # Would be calculated from time entries
                'utilization_percent': 0
            })
        
        return utilization


class ProjectMemberActionSerializer(serializers.Serializer):
    """Serializer for project member actions (add/remove/update)."""
    
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=ProjectMember.ROLE_CHOICES, required=False)
    hourly_rate = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        allow_null=True
    )
    allocation_percent = serializers.IntegerField(
        min_value=1, 
        max_value=100, 
        required=False
    )
    
    def validate_user_id(self, value):
        """Validate user exists."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for project statistics and analytics."""
    
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    budget_utilization = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    hours_by_user = serializers.SerializerMethodField()
    hours_by_week = serializers.SerializerMethodField()
    task_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    def get_hours_by_user(self, obj):
        """Get hours breakdown by team member."""
        # This would be implemented to return user-wise hour breakdown
        return []
    
    def get_hours_by_week(self, obj):
        """Get hours breakdown by week."""
        # This would be implemented to return weekly hour breakdown
        return []