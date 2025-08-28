# NovaTime

**Unified AI-First Time Tracking & Project Management Platform**

NovaTime is a comprehensive platform that combines time tracking, task management, performance intelligence, and team collaboration into a single, privacy-forward solution.

## Overview

NovaTime merges the best of Clockify, Toggl, Harvest, Connecteam, and Buddy Punch into one unified platform with:

- **Magic Timesheets**: AI-drafted timesheets from calendar, tickets, and commits
- **Performance Intelligence**: Explainable insights with fairness and privacy
- **Unified Workflow**: Timers + shifts + chat + lightweight PM in one tool
- **Privacy-First**: No surveillance, cohort-fair benchmarks, transparent controls

## Project Structure (Cleaned & Optimized)

```
novatime/ (Repository Root)
├── backend/               # Django application root
│   ├── main/              # Django project settings
│   │   ├── settings.py    # Main settings (cleaned up)
│   │   ├── urls.py        # URL configuration
│   │   ├── wsgi.py        # WSGI application
│   │   ├── asgi.py        # ASGI application
│   │   └── __init__.py
│   ├── tests/             # Backend test files (fixed settings)
│   │   ├── simple_db_test.py
│   │   └── test_db_connection.py
│   ├── static/            # Static files
│   ├── templates/         # Django templates
│   └── manage.py          # Django management script
├── frontend/              # React frontend (design system based)
│   ├── public/            # Static assets
│   │   ├── icons/         # Icon assets
│   │   └── images/        # Image assets
│   ├── src/               # Source code
│   │   ├── components/    # Organized by type
│   │   │   ├── ui/        # Basic UI components
│   │   │   ├── layout/    # Layout components
│   │   │   ├── forms/     # Form components
│   │   │   └── charts/    # Chart components
│   │   ├── pages/         # Feature-based pages
│   │   │   ├── auth/      # Authentication pages
│   │   │   ├── dashboard/ # Main dashboard
│   │   │   ├── tasks/     # Task management
│   │   │   ├── time/      # Time tracking
│   │   │   ├── approvals/ # Approval workflows
│   │   │   ├── reports/   # Reports and analytics
│   │   │   ├── chat/      # Team chat with @ai
│   │   │   └── admin/     # Admin interfaces
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API services
│   │   ├── styles/        # CSS with design tokens
│   │   │   ├── index.css  # Main stylesheet
│   │   │   └── tokens.css # Design token definitions
│   │   ├── utils/         # Utility functions
│   │   └── types/         # TypeScript type definitions
│   ├── package.json       # Node.js dependencies
│   ├── vite.config.ts     # Vite configuration
│   ├── tailwind.config.js # Tailwind CSS config with tokens
│   └── tsconfig.json      # TypeScript configuration
├── sample/                # Reference implementations (cleaned)
│   ├── ai-chat-starter-react-sse/      # Main AI chat reference
│   ├── ai-chat-starter-react-sse-e2e/  # E2E testing example
│   ├── ai-ui-full-bundle/              # Complete UI specifications
│   ├── reactflow-crewai-starter/       # Flow diagram components
│   └── reactflow-crewai-starter-e2e/   # Flow testing
├── docs/                  # Documentation
│   └── working-documents/ # Implementation plans and specs
│       ├── planning/      # Implementation plans
│       └── sample-design/ # Design system documentation
├── tasks/                 # Standalone tasks system
├── .env.example           # Environment variables template
├── .env                   # Local environment (created)
├── docker-compose.yml     # Docker development setup
├── Dockerfile             # Docker image definition
├── pytest.ini            # pytest configuration
├── requirements.txt       # Python dependencies (cleaned)
└── README.md              # This file
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