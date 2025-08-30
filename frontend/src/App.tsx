import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import { AppShell } from './components/layout';
import { TimerCard, TaskCard, Card, CardHeader, CardTitle, CardContent, Button } from './components/ui';

// Import page components
import Dashboard from './pages/dashboard';
import TimesheetPage from './pages/time';
import TasksPage from './pages/tasks';
import ApprovalsPage from './pages/approvals';
import ReportsPage from './pages/reports';
import ChatPage from './pages/chat';
import AdminPage from './pages/admin';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Mock data for demonstration
  const sampleTask = {
    id: '1',
    title: 'Implement user authentication',
    description: 'Add OAuth2 and JWT token support for secure user authentication',
    status: 'in_progress' as const,
    priority: 'high' as const,
    estimatedHours: 8,
    assignee: {
      id: '1',
      name: 'John Doe',
      avatar: undefined
    },
    dueDate: new Date('2025-08-30'),
    labels: [
      { id: '1', name: 'Backend', color: '#3b82f6' },
      { id: '2', name: 'Security', color: '#ef4444' }
    ]
  };

  // Dashboard content for the home route
  const DashboardContent = () => (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Welcome to NovaTime
        </h1>
        <p className="text-[var(--text-muted)]">
          Your AI-first time tracking and project management platform
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Active Timer */}
        <Card>
          <CardHeader>
            <CardTitle>Active Timer</CardTitle>
          </CardHeader>
          <CardContent>
            <TimerCard
              isRunning={true}
              project={{
                id: '1',
                name: 'NovaTime Development',
                color: '#22c55e'
              }}
              task={{
                id: '1',
                title: 'Frontend Component Library'
              }}
              description="Building reusable UI components with design tokens"
              elapsed="02:34:12"
              onStop={() => console.log('Stop timer')}
              onPause={() => console.log('Pause timer')}
              onEdit={() => console.log('Edit timer')}
            />
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Today's Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)]">Total Time</span>
                <span className="font-mono font-bold text-lg text-[var(--text)]">07:42:30</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)]">Billable Hours</span>
                <span className="font-mono font-bold text-lg text-[var(--success)]">06:15:45</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--text-muted)]">Tasks Completed</span>
                <span className="font-bold text-lg text-[var(--text)]">3</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Current Tasks */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold text-[var(--text)]">Current Tasks</h2>
          <Button variant="primary">
            ➕ Add Task
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <TaskCard
            task={sampleTask}
            onTaskClick={(id) => console.log('Open task:', id)}
            onStartTimer={(id) => console.log('Start timer for task:', id)}
          />

          <TaskCard
            task={{
              ...sampleTask,
              id: '2',
              title: 'Design timesheet interface',
              status: 'todo',
              priority: 'medium',
              labels: [{ id: '3', name: 'Design', color: '#8b5cf6' }]
            }}
            onTaskClick={(id) => console.log('Open task:', id)}
            onStartTimer={(id) => console.log('Start timer for task:', id)}
          />

          <TaskCard
            task={{
              ...sampleTask,
              id: '3',
              title: 'Setup CI/CD pipeline',
              status: 'done',
              priority: 'low',
              labels: [{ id: '4', name: 'DevOps', color: '#10b981' }]
            }}
            onTaskClick={(id) => console.log('Open task:', id)}
            onStartTimer={(id) => console.log('Start timer for task:', id)}
          />
        </div>
      </div>
    </div>
  );

  return (
    <Router>
      <Routes>
        {/* Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Main Application Routes */}
        <Route path="/" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <DashboardContent />
          </AppShell>
        } />

        <Route path="/dashboard" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <Dashboard />
          </AppShell>
        } />

        <Route path="/time" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <TimesheetPage />
          </AppShell>
        } />

        <Route path="/tasks" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <TasksPage />
          </AppShell>
        } />

        <Route path="/approvals" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <ApprovalsPage />
          </AppShell>
        } />

        <Route path="/reports" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <ReportsPage />
          </AppShell>
        } />

        <Route path="/chat" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <ChatPage />
          </AppShell>
        } />

        <Route path="/admin" element={
          <AppShell
            sidebarOpen={sidebarOpen}
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            <AdminPage />
          </AppShell>
        } />
      </Routes>
    </Router>
  );
}

export default App;