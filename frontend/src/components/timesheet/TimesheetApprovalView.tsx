import React, { useState, useEffect } from 'react';
import { Button, Card, CardHeader, CardTitle, CardContent } from '../ui';

interface TimesheetApproval {
  id: string;
  approver: string;
  approver_name: string;
  approver_email: string;
  status: 'pending' | 'approved' | 'rejected' | 'changes_requested';
  comments: string;
  created_at: string;
  decided_at: string | null;
}

interface TimesheetForApproval {
  id: string;
  user_name: string;
  user_email: string;
  workspace_name: string;
  start_date: string;
  end_date: string;
  status: 'submitted' | 'approved' | 'rejected';
  total_hours: number;
  billable_hours: number;
  overtime_hours: number;
  submitted_at: string;
  notes: string;
  approvals: TimesheetApproval[];
}

interface TimesheetApprovalProps {
  workspaceId?: string;
}

export const TimesheetApprovalView: React.FC<TimesheetApprovalProps> = ({ workspaceId }) => {
  const [pendingTimesheets, setPendingTimesheets] = useState<TimesheetForApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingApprovals();
  }, [workspaceId]);

  const fetchPendingApprovals = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (workspaceId) {
        params.append('workspace', workspaceId);
      }
      
      const response = await fetch(
        `/api/v1/timesheets/timesheets/pending_approvals/?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch pending approvals');
      }
      
      const data = await response.json();
      setPendingTimesheets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleApprovalAction = async (
    timesheetId: string, 
    action: 'approve' | 'reject' | 'request_changes',
    comments: string = ''
  ) => {
    try {
      setProcessingId(timesheetId);
      
      const response = await fetch(
        `/api/v1/timesheets/timesheets/${timesheetId}/approve/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action,
            comments
          }),
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to ${action} timesheet`);
      }
      
      // Refresh the list
      await fetchPendingApprovals();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} timesheet`);
    } finally {
      setProcessingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted': return 'var(--warning)';
      case 'approved': return 'var(--success)';
      case 'rejected': return 'var(--error)';
      default: return 'var(--text)';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-[var(--text-muted)]">Loading pending approvals...</div>
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--text)]">
          Timesheet Approvals
        </h1>
        <div className="text-sm text-[var(--text-muted)]">
          {pendingTimesheets.length} pending approval{pendingTimesheets.length !== 1 ? 's' : ''}
        </div>
      </div>

      {pendingTimesheets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-6xl mb-4">✅</div>
            <div className="text-xl font-medium text-[var(--text)] mb-2">All caught up!</div>
            <div className="text-[var(--text-muted)]">
              No timesheets are currently pending your approval.
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {pendingTimesheets.map((timesheet) => (
            <TimesheetApprovalCard
              key={timesheet.id}
              timesheet={timesheet}
              onAction={handleApprovalAction}
              isProcessing={processingId === timesheet.id}
              formatDate={formatDate}
              formatDateTime={formatDateTime}
              getStatusColor={getStatusColor}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface TimesheetApprovalCardProps {
  timesheet: TimesheetForApproval;
  onAction: (id: string, action: 'approve' | 'reject' | 'request_changes', comments?: string) => void;
  isProcessing: boolean;
  formatDate: (date: string) => string;
  formatDateTime: (date: string) => string;
  getStatusColor: (status: string) => string;
}

const TimesheetApprovalCard: React.FC<TimesheetApprovalCardProps> = ({
  timesheet,
  onAction,
  isProcessing,
  formatDate,
  formatDateTime,
  getStatusColor
}) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState('');
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'request_changes' | null>(null);

  const handleAction = (action: 'approve' | 'reject' | 'request_changes') => {
    if (action === 'approve') {
      onAction(timesheet.id, action);
    } else {
      setActionType(action);
      setShowComments(true);
    }
  };

  const handleSubmitWithComments = () => {
    if (actionType && (comments.trim() || actionType === 'approve')) {
      onAction(timesheet.id, actionType, comments);
      setShowComments(false);
      setComments('');
      setActionType(null);
    }
  };

  const billablePercentage = timesheet.total_hours > 0 
    ? Math.round((timesheet.billable_hours / timesheet.total_hours) * 100)
    : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{timesheet.user_name}</CardTitle>
            <div className="text-sm text-[var(--text-muted)] mt-1">
              {timesheet.user_email} • {timesheet.workspace_name}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-[var(--text-muted)]">
              {formatDate(timesheet.start_date)} - {formatDate(timesheet.end_date)}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Submitted {formatDateTime(timesheet.submitted_at)}
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Hours Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-[var(--primary)]">{timesheet.total_hours}h</div>
            <div className="text-sm text-[var(--text-muted)]">Total Hours</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-[var(--success)]">{timesheet.billable_hours}h</div>
            <div className="text-sm text-[var(--text-muted)]">Billable Hours</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-[var(--warning)]">{timesheet.overtime_hours}h</div>
            <div className="text-sm text-[var(--text-muted)]">Overtime</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-[var(--info)]">{billablePercentage}%</div>
            <div className="text-sm text-[var(--text-muted)]">Billable %</div>
          </div>
        </div>

        {/* Notes */}
        {timesheet.notes && (
          <div className="mb-6 p-4 bg-[var(--bg-elev)] rounded-lg border border-[var(--border)]">
            <div className="text-sm font-medium text-[var(--text)] mb-2">Employee Notes:</div>
            <div className="text-sm text-[var(--text-muted)]">{timesheet.notes}</div>
          </div>
        )}

        {/* Comments Input */}
        {showComments && (
          <div className="mb-6 p-4 bg-[var(--bg-elev)] rounded-lg border border-[var(--border)]">
            <div className="text-sm font-medium text-[var(--text)] mb-2">
              {actionType === 'reject' ? 'Rejection Reason:' : 'Comments:'}
            </div>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder={actionType === 'reject' 
                ? 'Please provide a reason for rejection...' 
                : 'Add comments (optional)...'
              }
              className="w-full p-3 border border-[var(--border)] rounded-md bg-[var(--bg)] text-[var(--text)] placeholder-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none"
              rows={3}
            />
            <div className="flex justify-end space-x-2 mt-3">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  setShowComments(false);
                  setComments('');
                  setActionType(null);
                }}
              >
                Cancel
              </Button>
              <Button 
                size="sm"
                onClick={handleSubmitWithComments}
                disabled={actionType === 'reject' && !comments.trim()}
              >
                {actionType === 'reject' ? 'Reject' : actionType === 'request_changes' ? 'Request Changes' : 'Submit'}
              </Button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3">
          <Button
            variant="ghost"
            onClick={() => handleAction('request_changes')}
            disabled={isProcessing}
          >
            Request Changes
          </Button>
          <Button
            variant="secondary"
            onClick={() => handleAction('reject')}
            disabled={isProcessing}
          >
            Reject
          </Button>
          <Button
            onClick={() => handleAction('approve')}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Approve'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};