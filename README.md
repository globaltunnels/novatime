# NovaTime

**Unified AI-First Time Tracking & Project Management Platform**

NovaTime is a comprehensive platform that combines time tracking, task management, performance intelligence, and team collaboration into a single, privacy-forward solution.

## Overview

NovaTime merges the best of Clockify, Toggl, Harvest, Connecteam, and Buddy Punch into one unified platform with:

- **Magic Timesheets**: AI-drafted timesheets from calendar, tickets, and commits
- **Performance Intelligence**: Explainable insights with fairness and privacy
- **Unified Workflow**: Timers + shifts + chat + lightweight PM in one tool
- **Privacy-First**: No surveillance, cohort-fair benchmarks, transparent controls

## Project Structure

```
novatime/ (Repository Root)
├── backend/               # Django application root
│   ├── main/              # Django project settings
│   │   ├── settings.py    # Main settings
│   │   ├── urls.py        # URL configuration
│   │   ├── wsgi.py        # WSGI application
│   │   ├── asgi.py        # ASGI application
│   │   └── __init__.py
│   ├── ai_services/       # AI services integration
│   │   ├── models.py      # AI service models
│   │   ├── views.py       # AI service API endpoints
│   │   ├── serializers.py # AI service serializers
│   │   ├── services.py    # AI service business logic
│   │   └── urls.py        # AI service URL patterns
│   ├── chat/              # Real-time chat functionality
│   │   ├── models.py      # Chat models
│   │   ├── views.py       # Chat API endpoints
│   │   ├── serializers.py # Chat serializers
│   │   └── signals.py     # Chat signals
│   ├── iam/               # Identity Access Management
│   │   ├── models.py      # User and authentication models
│   │   ├── views.py       # Authentication views
│   │   ├── serializers.py # User serializers
│   │   ├── admin.py       # Django admin configuration
│   │   └── urls.py        # IAM URL patterns
│   ├── organizations/     # Multi-tenant organizations
│   │   ├── models.py      # Organization models
│   │   ├── views.py       # Organization API endpoints
│   │   ├── admin.py       # Organization admin
│   │   └── tests.py       # Organization tests
│   ├── projects/          # Project management
│   │   ├── models.py      # Project models
│   │   ├── views.py       # Project API endpoints
│   │   ├── serializers.py # Project serializers
│   │   ├── admin.py       # Project admin
│   │   ├── urls.py        # Project URL patterns
│   │   └── tests.py       # Project tests
│   ├── tasks/             # Task management
│   │   ├── models.py      # Task models
│   │   ├── views.py       # Task API endpoints
│   │   ├── admin.py       # Task admin
│   │   └── tests.py       # Task tests
│   ├── time_entries/      # Time tracking entries
│   │   ├── models.py      # Time entry models
│   │   ├── views.py       # Time entry API endpoints
│   │   ├── admin.py       # Time entry admin
│   │   └── tests.py       # Time entry tests
│   ├── timesheets/        # Timesheet management
│   │   ├── models.py      # Timesheet models
│   │   ├── views.py       # Timesheet API endpoints
│   │   ├── serializers.py # Timesheet serializers
│   │   ├── urls.py        # Timesheet URL patterns
│   │   └── tests.py       # Timesheet tests
│   ├── websocket_server/ # WebSocket server for real-time features
│   │   ├── consumers.py   # WebSocket consumers
│   │   └── routing.py     # WebSocket routing
│   ├── tests/             # Backend test files
│   │   ├── conftest.py    # Test configuration
│   │   ├── pytest.ini     # Pytest configuration
│   │   └── test_*.py      # Individual test files
│   ├── static/            # Static files
│   ├── templates/         # Django templates
│   ├── .env.example       # Environment variables template
│   ├── requirements.txt   # Python dependencies
│   └── manage.py          # Django management script
├── frontend/              # React frontend
│   ├── public/            # Static assets
│   │   ├── icons/         # Icon assets
│   │   └── images/        # Image assets
│   ├── src/               # Source code
│   │   ├── components/    # UI components
│   │   │   ├── ui/        # Basic UI components
│   │   │   ├── layout/    # Layout components
│   │   │   ├── forms/     # Form components
│   │   │   ├── charts/    # Chart components
│   │   │   └── timesheet/ # Timesheet-specific components
│   │   ├── pages/         # Feature-based pages
│   │   │   ├── auth/      # Authentication pages
│   │   │   ├── dashboard/ # Main dashboard
│   │   │   ├── tasks/     # Task management
│   │   │   ├── time/      # Time tracking
│   │   │   ├── approvals/ # Approval workflows
│   │   │   ├── reports/   # Reports and analytics
│   │   │   ├── chat/      # Team chat
│   │   │   └── admin/     # Admin interfaces
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API services
│   │   ├── styles/        # CSS styles
│   │   ├── utils/         # Utility functions
│   │   └── types/         # TypeScript definitions
│   ├── tests/             # Frontend test files
│   ├── package.json       # Node.js dependencies
│   └── tsconfig.json      # TypeScript configuration
├── playwright/            # End-to-end testing
│   ├── tests/             # E2E test files
│   │   └── pages/         # Page object models
│   ├── playwright-report/ # Test reports
│   └── test-results/      # Test artifacts
├── docs/                  # Documentation
├── tasks/                 # Standalone tasks system
├── deploy/                # Docker deployment files
│   ├── docker-compose.yml # Docker development setup
│   └── Dockerfile         # Docker image definition
├── .gitignore            # Git ignore rules
├── .python-version       # Python version specification
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Python 3.12.11 (managed via pyenv)
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend development)

### Backend Setup

```bash
# Using pyenv to set Python version
pyenv install 3.12.11
pyenv virtualenv 3.12.11 novatime
pyenv local novatime

# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your database and other settings

# Navigate to backend directory
cd backend

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Data Migration (from Oracle)

*Note: Migration script is under development. Please check with the development team for current migration procedures.*

```bash
# Set Oracle environment variables in .env
export ORACLE_USERNAME="amprod"
export ORACLE_PASSWORD="sun66rise$"
export ORACLE_HOST="apdev.cpxgji6lqffb.us-east-1.rds.amazonaws.com"
export ORACLE_PORT="1521"
export ORACLE_SERVICE="ORCL"

# Migration script will be available in the root directory
# python migration_script.py
# python migration_script.py --dry-run
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Development

### Code Quality

- **Backend**: Black, isort, flake8, mypy
- **Frontend**: ESLint, Prettier
- **Testing**: pytest, Jest, Playwright

### Running Tests

```bash
# Backend tests
python manage.py test

# Frontend tests
cd frontend && npm test

# E2E tests
npx playwright test
```

### CI/CD

The project uses GitHub Actions for continuous integration with:
- Automated testing
- Code quality checks
- Security scanning
- Dependency vulnerability checks
- SBOM generation

## Documentation

- [Business Plan & Technical Specification](docs/working_documents/planning/)
- [API Documentation](docs/specification/backend/api/)
- [Architecture Overview](docs/)

## Contributing

1. Follow [Conventional Commits](https://www.conventionalcommits.org/)
2. Use the provided PR checklist
3. Ensure all tests pass
4. Update documentation as needed

## License

This project is proprietary software. See LICENSE file for details.

## Support

For support and questions:
- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/your-org/novatime/issues)
- Email: support@novatime.example.com

---

**NovaTime** - *From clock-in to cash-in. Time that fills itself.*