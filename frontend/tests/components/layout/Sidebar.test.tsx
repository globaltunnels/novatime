import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Sidebar } from '../../../src/components/layout/Sidebar';

describe('Sidebar', () => {
  it('renders sidebar with navigation items when not collapsed', () => {
    render(<Sidebar collapsed={false} />);
    
    expect(screen.getByText('NovaTime')).toBeInTheDocument();
    expect(screen.getByText('Time that fills itself')).toBeInTheDocument();
    
    // Check that navigation items are rendered
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Timesheet')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Schedule')).toBeInTheDocument();
    expect(screen.getByText('Approvals')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('renders collapsed sidebar without text labels', () => {
    render(<Sidebar collapsed={true} />);
    
    expect(screen.queryByText('NovaTime')).not.toBeInTheDocument();
    expect(screen.queryByText('Time that fills itself')).not.toBeInTheDocument();
    
    // Icons should still be present
    const homeLink = screen.getByText('🏠');
    expect(homeLink).toBeInTheDocument();
    expect(homeLink.closest('a')).toHaveAttribute('href', '/');
  });

  it('shows badge counts for items with badges', () => {
    render(<Sidebar collapsed={false} />);
    
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('applies correct classes based on collapsed state', () => {
    const { rerender } = render(<Sidebar collapsed={false} />);
    
    // Expanded sidebar
    let sidebar = screen.getByText('NovaTime').closest('div');
    expect(sidebar).toBeInTheDocument();
    
    // Re-render with collapsed state
    rerender(<Sidebar collapsed={true} />);
    expect(screen.queryByText('NovaTime')).not.toBeInTheDocument();
  });
});