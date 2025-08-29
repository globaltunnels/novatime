import React from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'priority-high' | 'priority-medium' | 'priority-low';
  children: React.ReactNode;
}

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variantClasses = {
      default: 'bg-[var(--bg)] border border-[var(--border)] text-[var(--text)]',
      success: 'bg-[var(--success)] text-white',
      warning: 'bg-[var(--warning)] text-white',
      error: 'bg-[var(--error)] text-white',
      info: 'bg-[var(--info)] text-white',
      'priority-high': 'bg-[var(--priority-high)] text-white',
      'priority-medium': 'bg-[var(--priority-medium)] text-white',
      'priority-low': 'bg-[var(--priority-low)] text-white'
    };
    
    return (
      <div
        ref={ref}
        className={clsx(
          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
          variantClasses[variant],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';