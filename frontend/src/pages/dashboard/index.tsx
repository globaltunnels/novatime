import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';

const Dashboard: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Dashboard
        </h1>
        <p className="text-[var(--text-muted)]">
          Overview of your time tracking and project progress
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Today's Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[var(--primary)]">7.5h</div>
            <p className="text-sm text-[var(--text-muted)]">+2.3h from yesterday</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Active Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[var(--success)]">3</div>
            <p className="text-sm text-[var(--text-muted)]">2 due this week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Pending Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[var(--warning)]">12</div>
            <p className="text-sm text-[var(--text-muted)]">5 high priority</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[var(--info)]">42.5h</div>
            <p className="text-sm text-[var(--text-muted)]">85% billable</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-[var(--success)] rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-[var(--text)]">Completed task: "Implement user authentication"</p>
                  <p className="text-xs text-[var(--text-muted)]">2 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-[var(--primary)] rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-[var(--text)]">Started timer for "Design system setup"</p>
                  <p className="text-xs text-[var(--text-muted)]">4 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-[var(--warning)] rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-[var(--text)]">Submitted timesheet for approval</p>
                  <p className="text-xs text-[var(--text-muted)]">1 day ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <button className="w-full p-3 text-left bg-[var(--bg-elev)] hover:bg-[var(--border)] rounded-md transition-colors">
                <div className="font-medium text-[var(--text)]">Start New Timer</div>
                <div className="text-sm text-[var(--text-muted)]">Begin tracking time on a task</div>
              </button>
              <button className="w-full p-3 text-left bg-[var(--bg-elev)] hover:bg-[var(--border)] rounded-md transition-colors">
                <div className="font-medium text-[var(--text)]">Create Task</div>
                <div className="text-sm text-[var(--text-muted)]">Add a new task to your project</div>
              </button>
              <button className="w-full p-3 text-left bg-[var(--bg-elev)] hover:bg-[var(--border)] rounded-md transition-colors">
                <div className="font-medium text-[var(--text)]">View Timesheet</div>
                <div className="text-sm text-[var(--text-muted)]">Review and submit your timesheet</div>
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;