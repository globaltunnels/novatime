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
│   ├── iam/               # Identity Access Management
│   ├── organizations/     # Multi-tenant organizations
│   ├── tasks/             # Task management
│   ├── time_entries/      # Time tracking
│   ├── timesheets/        # Timesheet processing
│   ├── attendance/        # Frontline attendance
│   ├── projects/          # Project management
│   ├── approvals/         # Approval workflows
│   ├── billing/           # Invoicing and billing
│   ├── conversations/     # Chat and messaging
│   ├── ai/                # AI services integration
│   ├── insights/          # Analytics and reporting
│   ├── integrations/      # External integrations
│   ├── seo/               # SEO content management
│   ├── abtests/           # A/B testing framework
│   ├── manage.py          # Django management script
│   ├── main/              # Django project settings
│   │   ├── settings.py    # Main settings
│   │   ├── urls.py        # URL configuration
│   │   ├── wsgi.py        # WSGI application
│   │   ├── asgi.py        # ASGI application
│   │   └── __init__.py
│   ├── static/            # Static files
│   ├── templates/         # Django templates
│   ├── media/             # User-uploaded files
│   ├── logs/              # Application logs
│   └── staticfiles/       # Collected static files
├── frontend/              # React frontend application
│   ├── public/           # Static assets
│   ├── src/              # Source code
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   └── services/     # API services
│   └── tests/            # Frontend tests
├── playwright/           # End-to-end tests
│   ├── tests/            # Test files
│   │   ├── auth/         # Authentication tests
│   │   ├── ui/           # UI tests
│   │   └── api/          # API tests
│   ├── fixtures/         # Test fixtures
│   ├── utils/            # Test utilities
│   ├── playwright.config.ts # Playwright configuration
│   └── package.json      # Node dependencies
├── tasks/                # Standalone tasks system
│   ├── copilot/          # AI copilot functionality
│   ├── taskexec/         # Task execution engine
│   └── out/              # Task output directory
├── docs/                 # Documentation and assets
├── scripts/              # Utility scripts
├── mcp-server/          # MCP server components
├── .env.example          # Environment variables template
├── docker-compose.yml    # Docker development setup
├── Dockerfile           # Docker image definition
├── pytest.ini           # pytest configuration
├── requirements.txt     # Python dependencies
└── README.md            # This file
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
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and other settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Data Migration (from Oracle)

```bash
# Set Oracle environment variables in .env
export ORACLE_USERNAME="amprod"
export ORACLE_PASSWORD="sun66rise$"
export ORACLE_HOST="apdev.cpxgji6lqffb.us-east-1.rds.amazonaws.com"
export ORACLE_PORT="1521"
export ORACLE_SERVICE="ORCL"

# Run migration
python migration_script.py

# Or run dry-run first
python migration_script.py --dry-run
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

- [Business Plan & Technical Specification](docs/planning/)
- [API Documentation](docs/novatime_openapi_v1.1.yaml)
- [Migration Guide](migration_plan.md)
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