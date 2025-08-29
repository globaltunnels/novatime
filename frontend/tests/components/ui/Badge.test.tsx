import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge } from '../../../src/components/ui/Badge';

describe('Badge', () => {
  it('renders badge with correct text', () => {
    render(<Badge>3</Badge>);
    
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('applies default variant classes', () => {
    render(<Badge>Default</Badge>);
    
    const badge = screen.getByText('Default');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-[var(--bg-elev)]');
  });

  it('applies primary variant classes', () => {
    render(<Badge variant="primary">Primary</Badge>);
    
    const badge = screen.getByText('Primary');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-[var(--primary)]');
  });

  it('applies success variant classes', () => {
    render(<Badge variant="success">Success</Badge>);
    
    const badge = screen.getByText('Success');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-[var(--success)]');
  });

  it('applies error variant classes', () => {
    render(<Badge variant="error">Error</Badge>);
    
    const badge = screen.getByText('Error');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-[var(--error)]');
  });

  it('applies warning variant classes', () => {
    render(<Badge variant="warning">Warning</Badge>);
    
    const badge = screen.getByText('Warning');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-[var(--warning)]');
  });
});