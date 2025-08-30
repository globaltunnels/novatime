import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';

const ReportsPage: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Reports & Analytics
        </h1>
        <p className="text-[var(--text-muted)]">
          View detailed reports and analytics about your time tracking and productivity
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reports Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--text-muted)]">
            Reports and analytics functionality will be implemented here.
            This will include time tracking reports, productivity metrics, and data visualization.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReportsPage;