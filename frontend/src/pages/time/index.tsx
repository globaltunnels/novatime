import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../../components/ui';
import { TimesheetApprovalView } from '../../components/timesheet';

const TimesheetPage: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Time Tracking
        </h1>
        <p className="text-[var(--text-muted)]">
          Track your time, manage timesheets, and view your work history
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full justify-start">
              ⏱️ Start Timer
            </Button>
            <Button variant="secondary" className="w-full justify-start">
              📝 Manual Entry
            </Button>
            <Button variant="secondary" className="w-full justify-start">
              📊 View Reports
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Total Hours</span>
                <span className="font-bold text-[var(--text)]">42.5h</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Billable</span>
                <span className="font-bold text-[var(--success)]">36.1h</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Overtime</span>
                <span className="font-bold text-[var(--warning)]">6.4h</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Timer</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-4xl font-mono font-bold text-[var(--primary)] mb-4">
                02:34:12
              </div>
              <p className="text-sm text-[var(--text-muted)] mb-4">
                Frontend Component Library
              </p>
              <div className="flex space-x-2">
                <Button size="sm" variant="secondary">Pause</Button>
                <Button size="sm">Stop</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Timesheet Content */}
      <Card>
        <CardHeader>
          <CardTitle>Weekly Timesheet</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--text-muted)]">
            Timesheet functionality will be implemented here.
            This will include weekly time entry, project selection, and submission features.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default TimesheetPage;