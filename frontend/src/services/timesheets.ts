import apiClient from './api';

export interface TimesheetEntry {
  id: string;
  user: string;
  project: string;
  task: string;
  description: string;
  start_time: string;
  end_time: string | null;
  duration: number; // in minutes
  billable: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Timesheet {
  id: string;
  user: string;
  user_name: string;
  user_email: string;
  workspace_name: string;
  start_date: string;
  end_date: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  total_hours: number;
  billable_hours: number;
  overtime_hours: number;
  submitted_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  notes: string;
  entries: TimesheetEntry[];
  approvals: TimesheetApproval[];
}

export interface TimesheetApproval {
  id: string;
  approver: string;
  approver_name: string;
  approver_email: string;
  status: 'pending' | 'approved' | 'rejected' | 'changes_requested';
  comments: string;
  created_at: string;
  decided_at: string | null;
}

export interface CreateTimesheetEntryData {
  project: string;
  task: string;
  description: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  billable?: boolean;
  tags?: string[];
}

export interface UpdateTimesheetEntryData extends Partial<CreateTimesheetEntryData> {
  id: string;
}

export interface TimesheetFilters {
  start_date?: string;
  end_date?: string;
  status?: string;
  project?: string;
  user?: string;
}

class TimesheetsService {
  // Timesheet entries
  async getEntries(filters?: TimesheetFilters): Promise<TimesheetEntry[]> {
    return apiClient.get<TimesheetEntry[]>('/time_entries/time_entries/', filters);
  }

  async getEntry(id: string): Promise<TimesheetEntry> {
    return apiClient.get<TimesheetEntry>(`/time_entries/time_entries/${id}/`);
  }

  async createEntry(data: CreateTimesheetEntryData): Promise<TimesheetEntry> {
    return apiClient.post<TimesheetEntry>('/time_entries/time_entries/', data);
  }

  async updateEntry(data: UpdateTimesheetEntryData): Promise<TimesheetEntry> {
    const { id, ...updateData } = data;
    return apiClient.patch<TimesheetEntry>(`/time_entries/time_entries/${id}/`, updateData);
  }

  async deleteEntry(id: string): Promise<void> {
    return apiClient.delete(`/time_entries/time_entries/${id}/`);
  }

  // Timesheets
  async getTimesheets(filters?: TimesheetFilters): Promise<Timesheet[]> {
    return apiClient.get<Timesheet[]>('/timesheets/timesheets/', filters);
  }

  async getTimesheet(id: string): Promise<Timesheet> {
    return apiClient.get<Timesheet>(`/timesheets/timesheets/${id}/`);
  }

  async createTimesheet(data: {
    start_date: string;
    end_date: string;
    notes?: string;
  }): Promise<Timesheet> {
    return apiClient.post<Timesheet>('/timesheets/timesheets/', data);
  }

  async updateTimesheet(id: string, data: Partial<Timesheet>): Promise<Timesheet> {
    return apiClient.patch<Timesheet>(`/timesheets/timesheets/${id}/`, data);
  }

  async submitTimesheet(id: string): Promise<Timesheet> {
    return apiClient.post<Timesheet>(`/timesheets/timesheets/${id}/submit/`);
  }

  async approveTimesheet(id: string, data: {
    action: 'approve' | 'reject' | 'request_changes';
    comments?: string;
  }): Promise<Timesheet> {
    return apiClient.post<Timesheet>(`/timesheets/timesheets/${id}/approve/`, data);
  }

  async getPendingApprovals(workspaceId?: string): Promise<Timesheet[]> {
    const params = workspaceId ? { workspace: workspaceId } : {};
    return apiClient.get<Timesheet[]>('/timesheets/timesheets/pending_approvals/', params);
  }

  // Timer functionality
  async startTimer(data: {
    project: string;
    task: string;
    description: string;
    billable?: boolean;
    tags?: string[];
  }): Promise<TimesheetEntry> {
    return apiClient.post<TimesheetEntry>('/time_entries/timer/start/', data);
  }

  async stopTimer(entryId: string): Promise<TimesheetEntry> {
    return apiClient.post<TimesheetEntry>(`/time_entries/timer/${entryId}/stop/`);
  }

  async getActiveTimer(): Promise<TimesheetEntry | null> {
    try {
      return await apiClient.get<TimesheetEntry>('/time_entries/timer/active/');
    } catch (error) {
      // No active timer
      return null;
    }
  }

  // Reports and analytics
  async getTimesheetReport(filters: {
    start_date: string;
    end_date: string;
    user?: string;
    project?: string;
    group_by?: 'day' | 'week' | 'month';
  }): Promise<any> {
    return apiClient.get('/timesheets/reports/', filters);
  }

  async getProductivityMetrics(filters: {
    start_date: string;
    end_date: string;
    user?: string;
  }): Promise<any> {
    return apiClient.get('/timesheets/metrics/', filters);
  }

  // Bulk operations
  async bulkUpdateEntries(data: {
    entries: UpdateTimesheetEntryData[];
  }): Promise<TimesheetEntry[]> {
    return apiClient.post<TimesheetEntry[]>('/time_entries/time_entries/bulk_update/', data);
  }

  async bulkDeleteEntries(entryIds: string[]): Promise<void> {
    return apiClient.post('/time_entries/time_entries/bulk_delete/', { ids: entryIds });
  }

  // Export functionality
  async exportTimesheet(id: string, format: 'pdf' | 'csv' | 'xlsx'): Promise<Blob> {
    const response = await apiClient.get(`/timesheets/timesheets/${id}/export/?format=${format}`, undefined, {
      responseType: 'blob'
    });
    return response as any;
  }

  async exportTimesheetReport(filters: TimesheetFilters & { format: 'pdf' | 'csv' | 'xlsx' }): Promise<Blob> {
    const response = await apiClient.get('/timesheets/reports/export/', filters, {
      responseType: 'blob'
    });
    return response as any;
  }
}

// Create and export singleton instance
export const timesheetsService = new TimesheetsService();
export default timesheetsService;