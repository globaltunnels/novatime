# NovaTime Django Backend

This directory contains the Django backend for the NovaTime platform, organized as modular, reusable components.

## Directory Structure

```
backend/
├── manage.py                # Django management script
├── main/                    # Django project settings
│   ├── settings.py          # Main settings
│   ├── urls.py              # URL configuration
│   ├── wsgi.py              # WSGI application
│   ├── asgi.py              # ASGI application
│   └── __init__.py
├── ai_services/             # AI services integration
├── chat/                    # Real-time chat functionality
├── iam/                     # Identity Access Management
├── organizations/           # Multi-tenant organizations
├── projects/                # Project management
├── tasks/                   # Task management
├── time_entries/            # Time tracking entries
├── timesheets/              # Timesheet management
├── websocket_server/       # WebSocket server for real-time features
├── static/                  # Static files
├── templates/               # Django templates
├── tests/                   # Test files
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Django Management

To run Django management commands, navigate to the `backend/` directory:

```bash
cd backend
python manage.py [command]
```

For example:
```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Apps Overview

### Core Business Logic
- **ai_services**: AI services integration, automation, and smart suggestions
- **chat**: Real-time chat and messaging functionality
- **iam**: Identity Access Management, User management, authentication, and authorization
- **organizations**: Multi-tenant organization management and RBAC
- **projects**: Project management with timelines and dependencies
- **tasks**: Task management and assignment
- **time_entries**: Time tracking entries and idle detection
- **timesheets**: Timesheet management, submission, and approvals

### Supporting Systems
- **websocket_server**: WebSocket server for real-time features and communication

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

1. Create new app directory without hyphens (e.g., `new_feature`)
2. Add to `INSTALLED_APPS` in settings
3. Create basic app structure following the standards
4. Add URL patterns to main `urls.py`
5. Create comprehensive tests
6. Update API documentation

## Inter Communication

- Use Django signals for loose coupling
- Implement service layers for complex business logic
- Use REST APIs for inter communication when needed
- Document all inter dependencies

## Contributing

When working with apps:
1. Follow the established patterns and standards
2. Keep apps focused on single responsibilities
3. Write comprehensive tests
4. Update documentation for any API changes
5. Ensure proper error handling and logging