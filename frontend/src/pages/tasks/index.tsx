import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';

const TasksPage: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Tasks
        </h1>
        <p className="text-[var(--text-muted)]">
          Manage your tasks, track progress, and collaborate with your team
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Task Management</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--text-muted)]">
            Task management functionality will be implemented here.
            This will include task creation, assignment, progress tracking, and collaboration features.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default TasksPage;