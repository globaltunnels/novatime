import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';

const AdminPage: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Administration
        </h1>
        <p className="text-[var(--text-muted)]">
          Manage users, organizations, and system settings
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>User Management</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[var(--text-muted)]">
              Manage user accounts, roles, and permissions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[var(--text-muted)]">
              Configure organization settings and policies
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[var(--text-muted)]">
              Manage system settings and integrations
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminPage;