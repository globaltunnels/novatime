import React from 'react';
import { clsx } from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
  helpText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error, label, helpText, ...props }, ref) => {
    const inputId = React.useId();
    
    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-[var(--text)] mb-2"
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          className={clsx(
            'flex h-10 w-full rounded-md border border-[var(--border)] bg-[var(--bg-elev)] px-3 py-2 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-[var(--error)] focus-visible:ring-[var(--error)]',
            className
          )}
          ref={ref}
          {...props}
        />
        {helpText && !error && (
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {helpText}
          </p>
        )}
        {error && (
          <p className="mt-1 text-sm text-[var(--error)]">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  label?: string;
  helpText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, label, helpText, ...props }, ref) => {
    const textareaId = React.useId();
    
    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-[var(--text)] mb-2"
          >
            {label}
          </label>
        )}
        <textarea
          id={textareaId}
          className={clsx(
            'flex min-h-[80px] w-full rounded-md border border-[var(--border)] bg-[var(--bg-elev)] px-3 py-2 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-[var(--error)] focus-visible:ring-[var(--error)]',
            className
          )}
          ref={ref}
          {...props}
        />
        {helpText && !error && (
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {helpText}
          </p>
        )}
        {error && (
          <p className="mt-1 text-sm text-[var(--error)]">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';