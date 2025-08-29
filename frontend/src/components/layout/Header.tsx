import React from 'react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export interface HeaderProps {
  onSidebarToggle?: () => void;
}

export const Header: React.FC<HeaderProps> = () => {
  return (
    <header className="h-16 bg-[var(--bg-elev)] border-b border-[var(--border)] px-6 flex items-center justify-between">
      {/* Left section */}
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-[var(--text)]">
          Today - Wednesday, Aug 28
        </h2>
      </div>
      
      {/* Right section */}
      <div className="flex items-center gap-4">
        {/* Quick Actions */}
        <Button variant="primary" size="sm">
          ⏱️ Start Timer
        </Button>
        
        <Button variant="secondary" size="sm">
          ➕ Add Task
        </Button>
        
        {/* Notifications */}
        <div className="relative">
          <button className="p-2 rounded-lg hover:bg-[var(--bg)] transition-colors">
            🔔
          </button>
          <Badge 
            variant="error" 
            className="absolute -top-1 -right-1 text-xs min-w-[20px] h-5 flex items-center justify-center"
          >
            3
          </Badge>
        </div>
        
        {/* Theme Toggle */}
        <button className="p-2 rounded-lg hover:bg-[var(--bg)] transition-colors">
          🌙
        </button>
        
        {/* User Avatar */}
        <div className="w-8 h-8 bg-[var(--success)] rounded-full flex items-center justify-center text-white text-sm font-medium">
          JD
        </div>
      </div>
    </header>
  );
};