from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


def default_dict():
    """Default empty dictionary"""
    return {}


def default_list():
    """Default empty list"""
    return []


class AIModel(models.Model):
    """
    AI model configurations for different services.
    """
    MODEL_TYPES = [
        ('timesheet_generation', 'Timesheet Generation'),
        ('task_assignment', 'Task Assignment'),
        ('time_prediction', 'Time Prediction'),
        ('project_estimation', 'Project Estimation'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('productivity_analysis', 'Productivity Analysis'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('training', 'Training'),
        ('inactive', 'Inactive'),
        ('deprecated', 'Deprecated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Model configuration
    model_config = models.JSONField(default=default_dict)
    training_data_path = models.CharField(max_length=500, blank=True)
    model_file_path = models.CharField(max_length=500, blank=True)
    
    # Performance metrics
    accuracy_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    precision_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    recall_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_trained_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_models'
        unique_together = ['model_type', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_model_type_display()})"


class AIJob(models.Model):
    """
    AI processing jobs and their status.
    """
    JOB_TYPES = [
        ('timesheet_generation', 'Generate Timesheet'),
        ('task_assignment', 'Assign Tasks'),
        ('time_prediction', 'Predict Time'),
        ('project_estimation', 'Estimate Project'),
        ('anomaly_detection', 'Detect Anomalies'),
        ('productivity_analysis', 'Analyze Productivity'),
        ('model_training', 'Train Model'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Job context
    job_type = models.CharField(max_length=50, choices=JOB_TYPES)
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='ai_jobs'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='ai_jobs'
    )
    
    # Job configuration
    model = models.ForeignKey(
        AIModel,
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    input_data = models.JSONField(default=default_dict)
    output_data = models.JSONField(default=default_dict)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    
    # Results
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    result_metadata = models.JSONField(default=default_dict)
    
    class Meta:
        db_table = 'ai_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['workspace', 'job_type', '-created_at']),
            models.Index(fields=['status', 'priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.status} ({self.user.email})"


class SmartTimesheetSuggestion(models.Model):
    """
    AI-generated timesheet suggestions based on patterns and calendar integration.
    """
    SUGGESTION_TYPES = [
        ('pattern_based', 'Pattern Based'),
        ('calendar_sync', 'Calendar Sync'),
        ('activity_detection', 'Activity Detection'),
        ('project_deadline', 'Project Deadline'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('modified', 'Modified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='timesheet_suggestions'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timesheet_suggestions'
    )
    
    # Suggestion details
    suggestion_type = models.CharField(max_length=50, choices=SUGGESTION_TYPES)
    date = models.DateField()
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='timesheet_suggestions'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timesheet_suggestions'
    )
    
    # Time details
    suggested_start_time = models.TimeField()
    suggested_end_time = models.TimeField()
    suggested_duration_minutes = models.PositiveIntegerField()
    suggested_description = models.TextField()
    
    # AI metadata
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    reasoning = models.TextField()  # Why AI made this suggestion
    source_data = models.JSONField(default=default_dict)  # Source data used
    
    # User interaction
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user_feedback = models.TextField(blank=True)
    
    # Generated time entry (if accepted)
    generated_time_entry = models.ForeignKey(
        'time_entries.TimeEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_suggestions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'smart_timesheet_suggestions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'date', 'status']),
            models.Index(fields=['workspace', 'status', '-created_at']),
            models.Index(fields=['project', 'status']),
        ]
    
    def __str__(self):
        return f"Suggestion for {self.user.email} on {self.date} - {self.project.name}"


class TaskAssignmentRecommendation(models.Model):
    """
    AI-generated task assignment recommendations based on workload, skills, and performance.
    """
    RECOMMENDATION_TYPES = [
        ('workload_balancing', 'Workload Balancing'),
        ('skill_matching', 'Skill Matching'),
        ('performance_based', 'Performance Based'),
        ('deadline_urgency', 'Deadline Urgency'),
        ('collaboration_pattern', 'Collaboration Pattern'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('auto_applied', 'Auto Applied'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='assignment_recommendations'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='assignment_recommendations'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='assignment_recommendations'
    )
    
    # Recommendation details
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    recommended_assignee = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='task_recommendations'
    )
    
    # Alternative recommendations
    alternative_assignees = models.ManyToManyField(
        'iam.User',
        through='TaskAssignmentAlternative',
        related_name='alternative_task_recommendations'
    )
    
    # AI analysis
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    reasoning = models.TextField()
    analysis_data = models.JSONField(default=default_dict)
    
    # Predicted outcomes
    estimated_completion_time = models.DurationField(null=True, blank=True)
    predicted_quality_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    workload_impact = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    manager_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'task_assignment_recommendations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'status']),
            models.Index(fields=['recommended_assignee', 'status', '-created_at']),
            models.Index(fields=['workspace', 'status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Recommend {self.recommended_assignee.email} for {self.task.title}"


class TaskAssignmentAlternative(models.Model):
    """
    Alternative assignee recommendations with scores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recommendation = models.ForeignKey(
        TaskAssignmentRecommendation,
        on_delete=models.CASCADE,
        related_name='alternatives'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='assignment_alternatives'
    )
    
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    ranking = models.PositiveIntegerField()  # 1 = best alternative
    reasoning = models.TextField()
    
    class Meta:
        db_table = 'task_assignment_alternatives'
        unique_together = ['recommendation', 'user']
        ordering = ['ranking']


class AIInsight(models.Model):
    """
    AI-generated insights and analytics for productivity and performance.
    """
    INSIGHT_TYPES = [
        ('productivity_trend', 'Productivity Trend'),
        ('time_pattern', 'Time Pattern'),
        ('project_risk', 'Project Risk'),
        ('resource_optimization', 'Resource Optimization'),
        ('burnout_prediction', 'Burnout Prediction'),
        ('efficiency_opportunity', 'Efficiency Opportunity'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='ai_insights'
    )
    
    # Scope - can be user-specific, project-specific, or workspace-wide
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_insights'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_insights'
    )
    
    # Insight content
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    
    # Data and recommendations
    insight_data = models.JSONField(default=default_dict)
    recommendations = models.JSONField(default=default_list)
    
    # Confidence and validity
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # User interaction
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_insights'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'insight_type', '-created_at']),
            models.Index(fields=['user', 'is_acknowledged', '-created_at']),
            models.Index(fields=['project', 'severity', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_insight_type_display()}: {self.title}"