import React from 'react';
import { clsx } from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading = false, disabled, children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-all duration-[var(--duration-base)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';
    
    const variantClasses = {
      primary: 'bg-[var(--primary)] text-white hover:bg-[var(--color-brand-pressed)] focus-visible:ring-[var(--primary)]',
      secondary: 'bg-[var(--bg-elev)] border border-[var(--border)] text-[var(--text)] hover:bg-[var(--border)] focus-visible:ring-[var(--primary)]',
      ghost: 'text-[var(--text)] hover:bg-[var(--bg-elev)] focus-visible:ring-[var(--primary)]',
      destructive: 'bg-[var(--error)] text-white hover:bg-red-600 focus-visible:ring-[var(--error)]'
    };
    
    const sizeClasses = {
      sm: 'h-8 px-3 text-sm rounded-md',
      md: 'h-10 px-4 py-2',
      lg: 'h-11 px-8 text-lg'
    };
    
    return (
      <button
        className={clsx(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';