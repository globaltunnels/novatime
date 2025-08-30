import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';

const ChatPage: React.FC = () => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
          Team Chat
        </h1>
        <p className="text-[var(--text-muted)]">
          Communicate with your team and collaborate on projects
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Chat Interface</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[var(--text-muted)]">
            Real-time chat functionality will be implemented here.
            This will include team messaging, file sharing, and AI-powered assistance.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatPage;