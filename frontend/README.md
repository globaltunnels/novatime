# NovaTime Frontend

React-based frontend application for NovaTime time tracking and project management platform.

## Overview

The frontend provides a modern, responsive user interface for:
- Time entry and timesheet management
- Project and task tracking
- Team collaboration and chat
- Performance analytics and insights
- User management and settings
- Mobile-responsive design with PWA support

## Architecture

### Project Structure

```
frontend/
├── public/                 # Static assets served directly
│   ├── favicon.ico
│   ├── manifest.json      # PWA manifest
│   ├── robots.txt
│   └── index.html         # Main HTML template
├── src/                    # Source code
│   ├── components/         # Reusable UI components
│   │   ├── common/        # Shared components (buttons, inputs, etc.)
│   │   ├── layout/        # Layout components (header, sidebar, etc.)
│   │   ├── forms/         # Form components
│   │   └── dashboard/     # Dashboard-specific components
│   ├── pages/             # Page components (route-based)
│   │   ├── auth/          # Authentication pages
│   │   ├── dashboard/     # Main dashboard
│   │   ├── timesheets/    # Timesheet management
│   │   ├── projects/      # Project management
│   │   ├── team/          # Team management
│   │   └── settings/      # User settings
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.js     # Authentication hook
│   │   ├── useApi.js      # API communication hook
│   │   └── useLocalStorage.js # Local storage hook
│   ├── services/          # API service layer
│   │   ├── api.js         # Base API configuration
│   │   ├── auth.js        # Authentication services
│   │   ├── timesheets.js  # Timesheet services
│   │   ├── projects.js    # Project services
│   │   └── websocket.js   # Real-time communication
│   ├── styles/            # Styling files
│   │   ├── index.css      # Global styles
│   │   ├── theme.js       # Theme configuration
│   │   └── components/    # Component-specific styles
│   ├── assets/            # Static assets (images, icons, fonts)
│   │   ├── images/        # Image files
│   │   ├── icons/         # Icon files
│   │   └── fonts/         # Font files
│   ├── types/             # TypeScript type definitions
│   │   ├── index.ts       # Main type exports
│   │   ├── api.ts         # API response types
│   │   └── components.ts  # Component prop types
│   ├── utils/             # Utility functions
│   │   ├── date.js        # Date manipulation utilities
│   │   ├── format.js      # Data formatting utilities
│   │   ├── validation.js  # Form validation utilities
│   │   └── constants.js   # Application constants
│   ├── App.js             # Main application component
│   ├── index.js           # Application entry point
│   └── routes.js          # Route configuration
├── tests/                 # Test files
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   ├── fixtures/         # Test data fixtures
│   ├── utils/            # Test utilities
│   └── setup.js          # Test configuration
└── scripts/               # Build and development scripts
    ├── build.js          # Production build script
    ├── start.js          # Development server script
    ├── test.js           # Test runner script
    └── lint.js           # Linting script
```

### Key Technologies

- **React 18+**: UI framework with hooks
- **TypeScript**: Type safety and developer experience
- **Tailwind CSS**: Utility-first CSS framework
- **Material-UI (MUI)**: Component library
- **React Router**: Client-side routing
- **Redux Toolkit**: State management
- **React Query**: Server state management
- **Axios**: HTTP client
- **Socket.IO**: Real-time communication
- **PWA Support**: Service workers, offline capabilities
- **Vite**: Build tool and development server

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Git

### Installation

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API endpoints and other settings
   ```

4. **Start development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

## Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run type-check

# Format code
npm run format
```

### Code Quality

- **ESLint**: Code linting and style enforcement
- **Prettier**: Code formatting
- **TypeScript**: Type checking
- **Husky**: Git hooks for pre-commit checks
- **Commitlint**: Conventional commit message enforcement

### Testing

```bash
# Run unit tests
npm run test

# Run integration tests
npm run test:integration

# Run e2e tests
npm run test:e2e

# Run all tests
npm run test:all
```

### Component Development

#### Creating a New Component

1. **Create component file**:
   ```typescript
   // src/components/MyComponent.tsx
   import React from 'react';
   import { Box, Typography } from '@mui/material';

   interface MyComponentProps {
     title: string;
     onAction?: () => void;
   }

   const MyComponent: React.FC<MyComponentProps> = ({ title, onAction }) => {
     return (
       <Box>
         <Typography variant="h6">{title}</Typography>
         {onAction && (
           <Button onClick={onAction}>Action</Button>
         )}
       </Box>
     );
   };

   export default MyComponent;
   ```

2. **Add tests**:
   ```typescript
   // src/components/__tests__/MyComponent.test.tsx
   import { render, screen, fireEvent } from '@testing-library/react';
   import MyComponent from '../MyComponent';

   describe('MyComponent', () => {
     it('renders title correctly', () => {
       render(<MyComponent title="Test Title" />);
       expect(screen.getByText('Test Title')).toBeInTheDocument();
     });

     it('calls onAction when button is clicked', () => {
       const mockAction = jest.fn();
       render(<MyComponent title="Test" onAction={mockAction} />);

       fireEvent.click(screen.getByText('Action'));
       expect(mockAction).toHaveBeenCalledTimes(1);
     });
   });
   ```

3. **Add to component exports**:
   ```typescript
   // src/components/index.ts
   export { default as MyComponent } from './MyComponent';
   ```

## API Integration

### Base API Configuration

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
});

// Request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Service Layer Example

```typescript
// src/services/timesheets.ts
import api from './api';
import { Timesheet, TimeEntry } from '../types';

export const timesheetsService = {
  async getTimesheets(params?: {
    page?: number;
    page_size?: number;
    user_id?: string;
  }): Promise<{ results: Timesheet[]; count: number }> {
    const response = await api.get('/timesheets/', { params });
    return response.data;
  },

  async createTimesheet(data: Partial<Timesheet>): Promise<Timesheet> {
    const response = await api.post('/timesheets/', data);
    return response.data;
  },

  async updateTimesheet(id: string, data: Partial<Timesheet>): Promise<Timesheet> {
    const response = await api.patch(`/timesheets/${id}/`, data);
    return response.data;
  },

  async submitTimesheet(id: string): Promise<void> {
    await api.post(`/timesheets/${id}/submit/`);
  },
};
```

## State Management

### Redux Toolkit Setup

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import timesheetsReducer from './slices/timesheetsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    timesheets: timesheetsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### React Query for Server State

```typescript
// src/hooks/useTimesheets.ts
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { timesheetsService } from '../services/timesheets';

export const useTimesheets = (params?: any) => {
  return useQuery(['timesheets', params], () => timesheetsService.getTimesheets(params));
};

export const useCreateTimesheet = () => {
  const queryClient = useQueryClient();

  return useMutation(timesheetsService.createTimesheet, {
    onSuccess: () => {
      queryClient.invalidateQueries('timesheets');
    },
  });
};
```

## Styling

### Theme Configuration

```typescript
// src/styles/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb',
    },
    secondary: {
      main: '#22c55e',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
        },
      },
    },
  },
});
```

### Tailwind CSS Integration

```css
/* src/styles/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors;
  }
}
```

## PWA Features

### Service Worker

```typescript
// public/sw.js
const CACHE_NAME = 'novatime-v1';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/',
        '/static/js/bundle.js',
        '/static/css/main.css',
        '/manifest.json',
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
```

### Web App Manifest

```json
// public/manifest.json
{
  "name": "NovaTime",
  "short_name": "NovaTime",
  "description": "Unified time tracking and project management",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [
    {
      "src": "/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

## Deployment

### Build Optimization

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@mui/icons-material'],
          utils: ['axios', 'date-fns'],
        },
      },
    },
    sourcemap: true,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### Environment Variables

```bash
# .env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development
REACT_APP_VERSION=1.0.0
```

## Performance

### Optimization Techniques

1. **Code Splitting**: Route-based and component-based splitting
2. **Lazy Loading**: Images, components, and routes
3. **Caching**: API responses and static assets
4. **Bundle Analysis**: Webpack bundle analyzer
5. **Image Optimization**: WebP format, responsive images
6. **Service Worker**: Offline capabilities and caching

### Monitoring

- **Core Web Vitals**: LCP, FID, CLS monitoring
- **Error Tracking**: Sentry integration
- **Performance Monitoring**: Real user monitoring
- **Bundle Size**: Regular bundle analysis

## Accessibility

### WCAG 2.2 AA Compliance

- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: ARIA labels and roles
- **Color Contrast**: WCAG AA compliant colors
- **Focus Management**: Visible focus indicators
- **Semantic HTML**: Proper heading structure

### Implementation

```typescript
// Accessible button component
const AccessibleButton: React.FC<ButtonProps> = ({
  children,
  onClick,
  disabled,
  loading,
  ...props
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};
```

## Contributing

1. Follow the existing code style and patterns
2. Write tests for new components and features
3. Update TypeScript types for new APIs
4. Ensure accessibility compliance
5. Test across different browsers and devices
6. Update documentation for new features

## Troubleshooting

### Common Issues

1. **Build Errors**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify environment variables

2. **API Connection Issues**
   - Check backend server is running
   - Verify API endpoints in environment variables
   - Check CORS configuration

3. **Styling Issues**
   - Clear browser cache
   - Check CSS imports and Tailwind configuration
   - Verify theme configuration

### Development Tools

- **React DevTools**: Component inspection and profiling
- **Redux DevTools**: State management debugging
- **Lighthouse**: Performance and accessibility auditing
- **Browser DevTools**: Network, console, and performance monitoring

## Support

- **Documentation**: [../docs/](../docs/)
- **API Docs**: [../docs/novatime_swagger_ui_bundle/](../docs/novatime_swagger_ui_bundle/)
- **Issues**: [GitHub Issues](https://github.com/your-org/novatime/issues)

---

**NovaTime Frontend** - Modern React application for time tracking and project management.