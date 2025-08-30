import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import { TimesheetApprovalView } from '../../components/timesheet';

const ApprovalsPage: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Approvals
        </h1>
        <p className="text-[var(--text-muted)]">
          Review and approve timesheets, tasks, and other submissions
        </p>
      </div>

      <TimesheetApprovalView />
    </div>
  );
};

export default ApprovalsPage;