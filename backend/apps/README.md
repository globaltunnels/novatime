# NovaTime Django Apps

This directory contains all Django applications for the NovaTime platform, organized as modular, reusable components.

## Apps Overview

### Core Business Logic
- **accounts-app**: User management, authentication, and authorization
- **organizations-app**: Multi-tenant organization management and RBAC
- **tasks-app**: Task and project management with AI assignment
- **time-entries-app**: Time tracking entries and idle detection
- **timesheets-app**: Timesheet management, submission, and approvals
- **projects-app**: Project management with timelines and dependencies

### Specialized Features
- **attendance-app**: Frontline attendance tracking and kiosk support
- **approvals-app**: Approval workflows and exception handling
- **billing-app**: Invoicing, rates, budgets, and payment integration
- **conversations-app**: Real-time chat and messaging with @ai support
- **insights-app**: Performance intelligence and analytics
- **ai-app**: AI services, automation, and smart suggestions

### Supporting Systems
- **integrations-app**: External service integrations (Jira, GitHub, Slack, etc.)
- **seo-app**: SEO content management and marketing automation
- **abtests-app**: A/B testing framework for optimization

## App Structure Standards

Each app follows the standard Django app structure:

```
app-name/
├── __init__.py             # Package initialization
├── apps.py                 # App configuration
├── models.py               # Database models with UUID primary keys
├── serializers.py          # DRF serializers for API
├── views.py                # API views and class-based views
├── urls.py                 # URL patterns
├── admin.py                # Django admin configuration
├── forms.py                # Django forms (when needed)
├── signals.py              # Django signals
├── tasks.py                # Celery background tasks
├── utils.py                # Utility functions
├── constants.py            # App constants and enums
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_serializers.py
│   └── test_integration.py
├── migrations/             # Database migrations
├── templates/              # App-specific templates
├── static/                 # App-specific static files
└── README.md               # App documentation
```

## Development Guidelines

### Model Standards
- Use UUID for all user-facing primary keys
- Define `__str__` method for all models
- Include `Meta` class with `ordering` and other metadata
- Use proper `related_name` for foreign keys
- Implement soft delete where appropriate

### API Standards
- Use class-based views for complex logic
- Implement proper pagination for list endpoints
- Use DRF serializers for all input/output
- Include comprehensive error handling
- Document all endpoints with OpenAPI

### Testing Standards
- Write unit tests for all models and utilities
- Write integration tests for API endpoints
- Use factories for test data creation
- Maintain test coverage above 80%
- Run tests in isolated database

### Code Quality
- Follow PEP 8 for Python code
- Use type hints where possible
- Write comprehensive docstrings
- Use meaningful variable and function names
- Implement proper error handling and logging

## Adding New Apps

1. Create new app directory with hyphens (e.g., `new-feature-app`)
2. Add to `INSTALLED_APPS` in settings
3. Create basic app structure following the standards
4. Add URL patterns to main `urls.py`
5. Create comprehensive tests
6. Update API documentation

## Inter-App Communication

- Use Django signals for loose coupling
- Implement service layers for complex business logic
- Use REST APIs for inter-app communication when needed
- Document all inter-app dependencies

## Contributing

When working with apps:
1. Follow the established patterns and standards
2. Keep apps focused on single responsibilities
3. Write comprehensive tests
4. Update documentation for any API changes
5. Ensure proper error handling and logging