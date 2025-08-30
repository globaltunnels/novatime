import React, { useState, useEffect } from 'react';
import { Button, Card, CardHeader, CardTitle, CardContent } from '../ui';

interface TimesheetEntry {
  id: string;
  date: string;
  project: string;
  project_name: string;
  task?: string;
  task_title?: string;
  hours: number;
  description: string;
  is_billable: boolean;
}

interface DailySummary {
  date: string;
  day_name: string;
  total_hours: number;
  billable_hours: number;
  entries_count: number;
}

interface ProjectSummary {
  project_id: string;
  project_name: string;
  total_hours: number;
  billable_hours: number;
  entries_count: number;
}

interface WeeklyTotals {
  total_hours: number;
  billable_hours: number;
  overtime_hours: number;
  billable_percentage: number;
  average_daily_hours: number;
}

interface Timesheet {
  id: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'locked';
  start_date: string;
  end_date: string;
  total_hours: number;
  billable_hours: number;
  overtime_hours: number;
  can_submit: boolean;
  can_approve: boolean;
  entries: TimesheetEntry[];
}

interface WeeklyTimesheetData {
  timesheet: Timesheet;
  daily_summaries: DailySummary[];
  project_summaries: ProjectSummary[];
  weekly_totals: WeeklyTotals;
}

interface WeeklyTimesheetViewProps {
  weekStart: Date;
  workspaceId: string;
  onWeekChange: (date: Date) => void;
}

export const WeeklyTimesheetView: React.FC<WeeklyTimesheetViewProps> = ({
  weekStart,
  workspaceId,
  onWeekChange
}) => {
  const [timesheetData, setTimesheetData] = useState<WeeklyTimesheetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWeeklyTimesheet();
  }, [weekStart, workspaceId]);

  const fetchWeeklyTimesheet = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const weekStartStr = weekStart.toISOString().split('T')[0];
      const response = await fetch(
        `/api/v1/timesheets/timesheets/weekly_view/?week_start=${weekStartStr}&workspace=${workspaceId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch timesheet data');
      }
      
      const data = await response.json();
      setTimesheetData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitTimesheet = async () => {
    if (!timesheetData?.timesheet) return;
    
    try {
      const response = await fetch(
        `/api/v1/timesheets/timesheets/${timesheetData.timesheet.id}/submit/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            notes: ''
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to submit timesheet');
      }
      
      // Refresh data
      await fetchWeeklyTimesheet();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit timesheet');
    }
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(weekStart);
    newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    onWeekChange(newDate);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'var(--text-muted)';
      case 'submitted': return 'var(--warning)';
      case 'approved': return 'var(--success)';
      case 'rejected': return 'var(--error)';
      case 'locked': return 'var(--info)';
      default: return 'var(--text)';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-[var(--text-muted)]">Loading timesheet...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-[var(--error)]">{error}</div>
      </div>
    );
  }

  const timesheet = timesheetData?.timesheet;
  const dailySummaries = timesheetData?.daily_summaries || [];
  const projectSummaries = timesheetData?.project_summaries || [];
  const weeklyTotals = timesheetData?.weekly_totals;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => navigateWeek('prev')}
          >
            ← Previous Week
          </Button>
          <h1 className="text-2xl font-bold text-[var(--text)]">
            Week of {formatDate(weekStart.toISOString().split('T')[0])}
          </h1>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => navigateWeek('next')}
          >
            Next Week →
          </Button>
        </div>
        
        {timesheet && (
          <div className="flex items-center space-x-4">
            <span 
              className="px-3 py-1 rounded-full text-sm font-medium"
              style={{ 
                backgroundColor: `${getStatusColor(timesheet.status)}20`,
                color: getStatusColor(timesheet.status)
              }}
            >
              {timesheet.status.charAt(0).toUpperCase() + timesheet.status.slice(1)}
            </span>
            
            {timesheet.can_submit && (
              <Button onClick={handleSubmitTimesheet}>
                Submit Timesheet
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Weekly Summary */}
      {weeklyTotals && (
        <Card>
          <CardHeader>
            <CardTitle>Weekly Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--primary)]">{weeklyTotals.total_hours}h</div>
                <div className="text-sm text-[var(--text-muted)]">Total Hours</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--success)]">{weeklyTotals.billable_hours}h</div>
                <div className="text-sm text-[var(--text-muted)]">Billable Hours</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--warning)]">{weeklyTotals.overtime_hours}h</div>
                <div className="text-sm text-[var(--text-muted)]">Overtime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--info)]">{weeklyTotals.billable_percentage}%</div>
                <div className="text-sm text-[var(--text-muted)]">Billable %</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-[var(--text)]">{weeklyTotals.average_daily_hours}h</div>
                <div className="text-sm text-[var(--text-muted)]">Daily Avg</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Daily Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Day</th>
                  <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Date</th>
                  <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Total Hours</th>
                  <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Billable Hours</th>
                  <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Entries</th>
                </tr>
              </thead>
              <tbody>
                {dailySummaries.map((day) => (
                  <tr key={day.date} className="border-b border-[var(--border)] hover:bg-[var(--bg-elev)]">
                    <td className="py-3 px-3 text-[var(--text)] font-medium">{day.day_name}</td>
                    <td className="py-3 px-3 text-[var(--text-muted)]">{formatDate(day.date)}</td>
                    <td className="py-3 px-3 text-right text-[var(--text)]">{day.total_hours}h</td>
                    <td className="py-3 px-3 text-right text-[var(--success)]">{day.billable_hours}h</td>
                    <td className="py-3 px-3 text-right text-[var(--text-muted)]">{day.entries_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Project Summary */}
      {projectSummaries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Project Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Project</th>
                    <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Total Hours</th>
                    <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Billable Hours</th>
                    <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Entries</th>
                  </tr>
                </thead>
                <tbody>
                  {projectSummaries.map((project) => (
                    <tr key={project.project_id} className="border-b border-[var(--border)] hover:bg-[var(--bg-elev)]">
                      <td className="py-3 px-3 text-[var(--text)] font-medium">{project.project_name}</td>
                      <td className="py-3 px-3 text-right text-[var(--text)]">{project.total_hours}h</td>
                      <td className="py-3 px-3 text-right text-[var(--success)]">{project.billable_hours}h</td>
                      <td className="py-3 px-3 text-right text-[var(--text-muted)]">{project.entries_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Time Entries */}
      {timesheet?.entries && timesheet.entries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Time Entries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border)]">
                    <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Date</th>
                    <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Project</th>
                    <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Task</th>
                    <th className="text-left py-2 px-3 text-[var(--text)] font-medium">Description</th>
                    <th className="text-right py-2 px-3 text-[var(--text)] font-medium">Hours</th>
                    <th className="text-center py-2 px-3 text-[var(--text)] font-medium">Billable</th>
                  </tr>
                </thead>
                <tbody>
                  {timesheet.entries.map((entry) => (
                    <tr key={entry.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-elev)]">
                      <td className="py-3 px-3 text-[var(--text-muted)]">{formatDate(entry.date)}</td>
                      <td className="py-3 px-3 text-[var(--text)]">{entry.project_name}</td>
                      <td className="py-3 px-3 text-[var(--text-muted)]">{entry.task_title || '-'}</td>
                      <td className="py-3 px-3 text-[var(--text)] max-w-xs truncate">{entry.description || '-'}</td>
                      <td className="py-3 px-3 text-right text-[var(--text)] font-medium">{entry.hours}h</td>
                      <td className="py-3 px-3 text-center">
                        <span 
                          className={`inline-block w-3 h-3 rounded-full ${
                            entry.is_billable ? 'bg-[var(--success)]' : 'bg-[var(--text-muted)]'
                          }`}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {(!timesheet || timesheet.entries.length === 0) && (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-6xl mb-4">⏰</div>
            <div className="text-xl font-medium text-[var(--text)] mb-2">No time entries for this week</div>
            <div className="text-[var(--text-muted)] mb-6">
              Start tracking your time or import from your time entries to see data here.
            </div>
            <Button>
              Start Time Tracking
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};