import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from '../../../src/components/layout/Header';

describe('Header', () => {
  it('renders the header with correct title', () => {
    render(<Header />);
    
    expect(screen.getByText('Today - Wednesday, Aug 28')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    render(<Header />);
    
    expect(screen.getByText('⏱️ Start Timer')).toBeInTheDocument();
    expect(screen.getByText('➕ Add Task')).toBeInTheDocument();
  });

  it('renders notification badge with correct count', () => {
    render(<Header />);
    
    const badge = screen.getByText('3');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('absolute');
  });

  it('renders user avatar', () => {
    render(<Header />);
    
    const avatar = screen.getByText('JD');
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveClass('w-8', 'h-8');
  });
});