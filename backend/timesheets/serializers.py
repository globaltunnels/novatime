from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    Timesheet, TimesheetEntry, TimesheetApproval, 
    TimesheetException, TimesheetTemplate, TimesheetReminder
)
from time_entries.models import TimeEntry
from projects.models import Project
from tasks.models import Task


class TimesheetEntrySerializer(serializers.ModelSerializer):
    """Serializer for individual timesheet entries."""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TimesheetEntry
        fields = [
            'id', 'date', 'project', 'project_name', 'task', 'task_title',
            'hours', 'description', 'is_billable', 'hourly_rate', 'total_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate timesheet entry data."""
        # Ensure date is within timesheet period
        if hasattr(self, 'context') and 'timesheet' in self.context:
            timesheet = self.context['timesheet']
            if not (timesheet.start_date <= data['date'] <= timesheet.end_date):
                raise serializers.ValidationError(
                    f"Date must be between {timesheet.start_date} and {timesheet.end_date}"
                )
        
        # Validate hours
        if data.get('hours', 0) <= 0:
            raise serializers.ValidationError("Hours must be greater than 0")
        
        if data.get('hours', 0) > 24:
            raise serializers.ValidationError("Hours cannot exceed 24 per day")
        
        return data


class TimesheetApprovalSerializer(serializers.ModelSerializer):
    """Serializer for timesheet approvals."""
    
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    approver_email = serializers.CharField(source='approver.email', read_only=True)
    
    class Meta:
        model = TimesheetApproval
        fields = [
            'id', 'approver', 'approver_name', 'approver_email',
            'status', 'comments', 'approved_hours',
            'created_at', 'decided_at'
        ]
        read_only_fields = ['id', 'approver_name', 'approver_email', 'created_at']
    
    def update(self, instance, validated_data):
        """Update approval with decision timestamp."""
        if 'status' in validated_data and validated_data['status'] != 'pending':
            validated_data['decided_at'] = timezone.now()
        return super().update(instance, validated_data)


class TimesheetExceptionSerializer(serializers.ModelSerializer):
    """Serializer for timesheet exceptions."""
    
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = TimesheetException
        fields = [
            'id', 'exception_type', 'severity', 'status', 'title', 'description',
            'ai_detected', 'ai_confidence', 'resolved_by', 'resolved_by_name',
            'resolved_at', 'resolution_notes', 'created_at'
        ]
        read_only_fields = ['id', 'resolved_by_name', 'created_at']


class TimesheetSerializer(serializers.ModelSerializer):
    """Main timesheet serializer with nested entries and approvals."""
    
    entries = TimesheetEntrySerializer(many=True, read_only=True)
    approvals = TimesheetApprovalSerializer(many=True, read_only=True)
    exceptions = TimesheetExceptionSerializer(many=True, read_only=True)
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    
    # Calculated fields
    days_in_period = serializers.SerializerMethodField()
    submission_deadline = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()
    can_approve = serializers.SerializerMethodField()
    
    class Meta:
        model = Timesheet
        fields = [
            'id', 'user', 'user_name', 'user_email', 'workspace', 'workspace_name',
            'period_type', 'start_date', 'end_date', 'status',
            'total_hours', 'billable_hours', 'overtime_hours',
            'ai_generated', 'ai_confidence', 'ai_suggestions_count', 'ai_accepted_count',
            'submitted_at', 'submitted_by', 'approved_at', 'approved_by',
            'notes', 'rejection_reason',
            'entries', 'approvals', 'exceptions',
            'days_in_period', 'submission_deadline', 'is_overdue', 'can_submit', 'can_approve',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'user_email', 'workspace_name',
            'total_hours', 'billable_hours', 'overtime_hours',
            'submitted_at', 'submitted_by', 'approved_at', 'approved_by',
            'entries', 'approvals', 'exceptions',
            'days_in_period', 'submission_deadline', 'is_overdue', 'can_submit', 'can_approve',
            'created_at', 'updated_at'
        ]
    
    def get_days_in_period(self, obj):
        """Calculate number of days in the timesheet period."""
        return (obj.end_date - obj.start_date).days + 1
    
    def get_submission_deadline(self, obj):
        """Calculate submission deadline (end of period + 3 days)."""
        deadline = obj.end_date + timezone.timedelta(days=3)
        return deadline
    
    def get_is_overdue(self, obj):
        """Check if timesheet is overdue for submission."""
        if obj.status in ['submitted', 'approved', 'locked']:
            return False
        deadline = self.get_submission_deadline(obj)
        return timezone.now().date() > deadline
    
    def get_can_submit(self, obj):
        """Check if current user can submit this timesheet."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        return (
            obj.status == 'draft' and 
            obj.user == request.user and
            obj.total_hours > 0
        )
    
    def get_can_approve(self, obj):
        """Check if current user can approve this timesheet."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        # Check if user has approval permission for this workspace
        # This would be implemented based on your permission system
        return (
            obj.status == 'submitted' and
            obj.user != request.user
        )
    
    def validate(self, data):
        """Validate timesheet data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise serializers.ValidationError("End date must be after start date")
            
            # Validate period length based on period type
            period_length = (end_date - start_date).days + 1
            period_type = data.get('period_type', 'weekly')
            
            if period_type == 'weekly' and period_length != 7:
                raise serializers.ValidationError("Weekly timesheets must be exactly 7 days")
            elif period_type == 'bi_weekly' and period_length != 14:
                raise serializers.ValidationError("Bi-weekly timesheets must be exactly 14 days")
        
        return data


class TimesheetSubmissionSerializer(serializers.Serializer):
    """Serializer for timesheet submission."""
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate timesheet can be submitted."""
        timesheet = self.context.get('timesheet')
        if not timesheet:
            raise serializers.ValidationError("Timesheet context required")
        
        if timesheet.status != 'draft':
            raise serializers.ValidationError("Only draft timesheets can be submitted")
        
        if timesheet.total_hours <= 0:
            raise serializers.ValidationError("Cannot submit timesheet with no hours")
        
        return data


class TimesheetApprovalActionSerializer(serializers.Serializer):
    """Serializer for timesheet approval actions."""
    
    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_changes'])
    comments = serializers.CharField(required=False, allow_blank=True)
    approved_hours = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False,
        min_value=Decimal('0.01')
    )
    
    def validate(self, data):
        """Validate approval action."""
        action = data.get('action')
        
        if action in ['reject', 'request_changes'] and not data.get('comments'):
            raise serializers.ValidationError("Comments are required for rejection or change requests")
        
        return data


class TimesheetTemplateSerializer(serializers.ModelSerializer):
    """Serializer for timesheet templates."""
    
    class Meta:
        model = TimesheetTemplate
        fields = [
            'id', 'name', 'description', 'template_data',
            'is_active', 'use_count', 'last_used',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'use_count', 'last_used', 'created_at', 'updated_at']


class TimesheetGenerationSerializer(serializers.Serializer):
    """Serializer for generating timesheets from time entries."""
    
    user = serializers.UUIDField(required=False)
    workspace = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    period_type = serializers.ChoiceField(choices=['weekly', 'bi_weekly', 'monthly'])
    include_unbillable = serializers.BooleanField(default=True)
    template = serializers.UUIDField(required=False)
    
    def validate(self, data):
        """Validate timesheet generation parameters."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        # Validate date range is reasonable
        if (end_date - start_date).days > 31:
            raise serializers.ValidationError("Date range cannot exceed 31 days")
        
        return data


class WeeklyTimesheetViewSerializer(serializers.Serializer):
    """Serializer for weekly timesheet view with daily breakdowns."""
    
    timesheet = TimesheetSerializer(read_only=True)
    daily_summaries = serializers.SerializerMethodField()
    project_summaries = serializers.SerializerMethodField()
    weekly_totals = serializers.SerializerMethodField()
    
    def get_daily_summaries(self, obj):
        """Get daily hour summaries for the week."""
        timesheet = obj
        daily_data = []
        
        current_date = timesheet.start_date
        while current_date <= timesheet.end_date:
            day_entries = timesheet.entries.filter(date=current_date)
            daily_total = sum(entry.hours for entry in day_entries)
            daily_billable = sum(entry.hours for entry in day_entries if entry.is_billable)
            
            daily_data.append({
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'total_hours': daily_total,
                'billable_hours': daily_billable,
                'entries_count': day_entries.count()
            })
            current_date += timezone.timedelta(days=1)
        
        return daily_data
    
    def get_project_summaries(self, obj):
        """Get project-wise hour summaries."""
        timesheet = obj
        project_data = {}
        
        for entry in timesheet.entries.all():
            project_id = str(entry.project.id)
            if project_id not in project_data:
                project_data[project_id] = {
                    'project_id': project_id,
                    'project_name': entry.project.name,
                    'total_hours': Decimal('0.00'),
                    'billable_hours': Decimal('0.00'),
                    'entries_count': 0
                }
            
            project_data[project_id]['total_hours'] += entry.hours
            if entry.is_billable:
                project_data[project_id]['billable_hours'] += entry.hours
            project_data[project_id]['entries_count'] += 1
        
        return list(project_data.values())
    
    def get_weekly_totals(self, obj):
        """Get weekly totals and statistics."""
        timesheet = obj
        return {
            'total_hours': timesheet.total_hours,
            'billable_hours': timesheet.billable_hours,
            'overtime_hours': timesheet.overtime_hours,
            'billable_percentage': (
                round((timesheet.billable_hours / timesheet.total_hours) * 100, 1)
                if timesheet.total_hours > 0 else 0
            ),
            'average_daily_hours': (
                round(timesheet.total_hours / 7, 2)
                if timesheet.period_type == 'weekly' else None
            )
        }