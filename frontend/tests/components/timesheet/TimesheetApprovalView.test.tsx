import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TimesheetApprovalView } from '../../../src/components/timesheet/TimesheetApprovalView';

// Mock the useApproval hook
vi.mock('../../../src/hooks/useApproval', () => ({
  useApproval: () => ({
    timesheets: [
      {
        id: '1',
        user: {
          id: '1',
          name: 'John Doe',
          avatar: 'JD'
        },
        period: 'Aug 21 - Aug 27, 2023',
        total_hours: 40,
        billable_hours: 32,
        status: 'submitted',
        submitted_at: '2023-08-27T10:00:00Z'
      }
    ],
    isLoading: false,
    error: null,
    approveTimesheet: vi.fn(),
    rejectTimesheet: vi.fn(),
  })
}));

describe('TimesheetApprovalView', () => {
  it('renders approval view with timesheet data', () => {
    render(<TimesheetApprovalView />);
    
    expect(screen.getByText('Timesheet Approvals')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Aug 21 - Aug 27, 2023')).toBeInTheDocument();
  });

  it('displays correct hours information', () => {
    render(<TimesheetApprovalView />);
    
    expect(screen.getByText('40.0')).toBeInTheDocument();
    expect(screen.getByText('32.0')).toBeInTheDocument();
  });

  it('shows action buttons for approval', () => {
    render(<TimesheetApprovalView />);
    
    expect(screen.getByText('Approve')).toBeInTheDocument();
    expect(screen.getByText('Reject')).toBeInTheDocument();
  });

  it('displays correct status badge', () => {
    render(<TimesheetApprovalView />);
    
    const statusBadge = screen.getByText('submitted');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge).toHaveClass('px-2', 'py-1', 'rounded-full', 'text-xs', 'font-medium');
  });
});