import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AppShell } from '../../../src/components/layout/AppShell';

describe('AppShell', () => {
  it('renders children content', () => {
    render(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );
    
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders sidebar and header by default', () => {
    render(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );
    
    // Check that the main structure is rendered
    const appShell = screen.getByText('Test Content').closest('.min-h-screen');
    expect(appShell).toBeInTheDocument();
  });

  it('applies correct classes when sidebar is open', () => {
    render(
      <AppShell sidebarOpen={true}>
        <div>Test Content</div>
      </AppShell>
    );
    
    const sidebar = screen.getByText('Test Content').closest('.min-h-screen')?.firstChild;
    expect(sidebar).toHaveClass('w-64');
  });

  it('applies correct classes when sidebar is collapsed', () => {
    render(
      <AppShell sidebarOpen={false}>
        <div>Test Content</div>
      </AppShell>
    );
    
    const sidebar = screen.getByText('Test Content').closest('.min-h-screen')?.firstChild;
    expect(sidebar).toHaveClass('w-16');
  });
});