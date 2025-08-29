import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { WeeklyTimesheetView } from '../../../src/components/timesheet/WeeklyTimesheetView';

// Mock the useTimesheet hook since we're not testing the hook here
vi.mock('../../../src/hooks/useTimesheet', () => ({
  useTimesheet: () => ({
    timesheet: {
      id: '1',
      status: 'draft',
      start_date: '2023-08-21',
      end_date: '2023-08-27',
      total_hours: 40,
      billable_hours: 32,
      overtime_hours: 0,
      can_submit: true,
      can_approve: false,
      entries: [
        {
          id: '1',
          date: '2023-08-21',
          project: 'project1',
          project_name: 'Project Alpha',
          hours: 8,
          description: 'Work on feature',
          is_billable: true,
        }
      ]
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    submitTimesheet: vi.fn(),
    approveTimesheet: vi.fn(),
    rejectTimesheet: vi.fn(),
  })
}));

describe('WeeklyTimesheetView', () => {
  it('renders timesheet view with data', () => {
    render(<WeeklyTimesheetView />);
    
    // Check that key elements are rendered
    expect(screen.getByText('Weekly Timesheet')).toBeInTheDocument();
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('Work on feature')).toBeInTheDocument();
  });

  it('displays correct total hours', () => {
    render(<WeeklyTimesheetView />);
    
    expect(screen.getByText('40.0')).toBeInTheDocument();
  });

  it('displays correct billable hours', () => {
    render(<WeeklyTimesheetView />);
    
    expect(screen.getByText('32.0')).toBeInTheDocument();
  });

  it('shows submit button when timesheet can be submitted', () => {
    render(<WeeklyTimesheetView />);
    
    expect(screen.getByText('Submit Timesheet')).toBeInTheDocument();
  });
});