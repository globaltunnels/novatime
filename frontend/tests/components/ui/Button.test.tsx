import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Button } from '../../../src/components/ui/Button';

describe('Button', () => {
  it('renders button with correct text', () => {
    render(<Button>Click me</Button>);
    
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('applies primary variant classes', () => {
    render(<Button variant="primary">Primary Button</Button>);
    
    const button = screen.getByText('Primary Button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-[var(--primary)]');
  });

  it('applies secondary variant classes', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    
    const button = screen.getByText('Secondary Button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-[var(--bg)]');
  });

  it('applies correct size classes', () => {
    render(<Button size="sm">Small Button</Button>);
    
    const button = screen.getByText('Small Button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('px-3', 'py-1.5');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>);
    
    const button = screen.getByText('Disabled Button');
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Clickable Button</Button>);
    
    const button = screen.getByText('Clickable Button');
    button.click();
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});