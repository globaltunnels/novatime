import React from 'react';
import { clsx } from 'clsx';

export interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: string;
  href: string;
  active?: boolean;
  badge?: string;
}

const navigationItems: NavItem[] = [
  { id: 'home', label: 'Home', icon: '🏠', href: '/', active: true },
  { id: 'timesheet', label: 'Timesheet', icon: '📋', href: '/timesheet' },
  { id: 'projects', label: 'Projects', icon: '📁', href: '/projects' },
  { id: 'tasks', label: 'Tasks', icon: '✅', href: '/tasks', badge: '12' },
  { id: 'schedule', label: 'Schedule', icon: '📅', href: '/schedule' },
  { id: 'approvals', label: 'Approvals', icon: '✋', href: '/approvals', badge: '3' },
  { id: 'reports', label: 'Reports', icon: '📊', href: '/reports' },
  { id: 'chat', label: 'Chat', icon: '💬', href: '/chat' },
  { id: 'admin', label: 'Admin', icon: '⚙️', href: '/admin' }
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed = false, onToggle }) => {
  return (
    <div className={clsx(
      'h-screen bg-[var(--bg-elev)] border-r border-[var(--border)] flex flex-col',
      'transition-all duration-300'
    )}>
      {/* Logo Section */}
      <div className="p-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[var(--primary)] rounded-lg flex items-center justify-center text-white font-bold">
            N
          </div>
          {!collapsed && (
            <div>
              <h1 className="font-bold text-lg text-[var(--text)]">NovaTime</h1>
              <p className="text-xs text-[var(--text-muted)]">Time that fills itself</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navigationItems.map((item) => (
          <a
            key={item.id}
            href={item.href}
            className={clsx(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              item.active
                ? 'bg-[var(--primary)] text-white'
                : 'text-[var(--text)] hover:bg-[var(--bg)] hover:text-[var(--text)]'
            )}
            title={collapsed ? item.label : undefined}
          >
            <span className="text-lg">{item.icon}</span>
            {!collapsed && (
              <>
                <span className="flex-1">{item.label}</span>
                {item.badge && (
                  <span className="bg-[var(--error)] text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </a>
        ))}
      </nav>
      
      {/* User Section */}
      <div className="p-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[var(--success)] rounded-full flex items-center justify-center text-white text-sm font-medium">
            JD
          </div>
          {!collapsed && (
            <div className="flex-1">
              <p className="text-sm font-medium text-[var(--text)]">John Doe</p>
              <p className="text-xs text-[var(--text-muted)]">john@example.com</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Toggle Button */}
      {onToggle && (
        <button
          onClick={onToggle}
          className="absolute top-4 -right-3 w-6 h-6 bg-[var(--bg-elev)] border border-[var(--border)] rounded-full flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
        >
          {collapsed ? '→' : '←'}
        </button>
      )}
    </div>
  );
};