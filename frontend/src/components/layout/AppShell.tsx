import React from 'react';
import { clsx } from 'clsx';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export interface AppShellProps {
  children: React.ReactNode;
  sidebarOpen?: boolean;
  onSidebarToggle?: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  sidebarOpen = true,
  onSidebarToggle
}) => {
  return (
    <div className="min-h-screen bg-[var(--bg)] flex">
      {/* Sidebar */}
      <div className={clsx(
        'transition-all duration-300 ease-in-out',
        sidebarOpen ? 'w-64' : 'w-16'
      )}>
        <Sidebar collapsed={!sidebarOpen} onToggle={onSidebarToggle} />
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header onSidebarToggle={onSidebarToggle} />
        
        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};