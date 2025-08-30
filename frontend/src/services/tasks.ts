import apiClient from './api';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'review' | 'done' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimated_hours: number;
  actual_hours: number;
  assignee: string | null;
  assignee_name: string | null;
  reporter: string;
  reporter_name: string;
  project: string;
  project_name: string;
  parent_task: string | null;
  subtasks: Task[];
  tags: string[];
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  attachments: TaskAttachment[];
  comments: TaskComment[];
}

export interface TaskAttachment {
  id: string;
  filename: string;
  file_url: string;
  file_size: number;
  uploaded_by: string;
  uploaded_by_name: string;
  uploaded_at: string;
}

export interface TaskComment {
  id: string;
  content: string;
  author: string;
  author_name: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskData {
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  estimated_hours?: number;
  assignee?: string;
  project: string;
  parent_task?: string;
  tags?: string[];
  due_date?: string;
}

export interface UpdateTaskData extends Partial<CreateTaskData> {
  id: string;
  status?: 'todo' | 'in_progress' | 'review' | 'done' | 'cancelled';
}

export interface TaskFilters {
  status?: string;
  priority?: string;
  assignee?: string;
  project?: string;
  due_date_before?: string;
  due_date_after?: string;
  tags?: string[];
  search?: string;
}

class TasksService {
  // Task CRUD operations
  async getTasks(filters?: TaskFilters): Promise<Task[]> {
    return apiClient.get<Task[]>('/tasks/tasks/', filters);
  }

  async getTask(id: string): Promise<Task> {
    return apiClient.get<Task>(`/tasks/tasks/${id}/`);
  }

  async createTask(data: CreateTaskData): Promise<Task> {
    return apiClient.post<Task>('/tasks/tasks/', data);
  }

  async updateTask(data: UpdateTaskData): Promise<Task> {
    const { id, ...updateData } = data;
    return apiClient.patch<Task>(`/tasks/tasks/${id}/`, updateData);
  }

  async deleteTask(id: string): Promise<void> {
    return apiClient.delete(`/tasks/tasks/${id}/`);
  }

  // Task status operations
  async startTask(id: string): Promise<Task> {
    return apiClient.post<Task>(`/tasks/tasks/${id}/start/`);
  }

  async completeTask(id: string): Promise<Task> {
    return apiClient.post<Task>(`/tasks/tasks/${id}/complete/`);
  }

  async assignTask(id: string, assigneeId: string): Promise<Task> {
    return apiClient.post<Task>(`/tasks/tasks/${id}/assign/`, { assignee: assigneeId });
  }

  async unassignTask(id: string): Promise<Task> {
    return apiClient.post<Task>(`/tasks/tasks/${id}/unassign/`);
  }

  // Subtasks
  async getSubtasks(parentId: string): Promise<Task[]> {
    return apiClient.get<Task[]>(`/tasks/tasks/${parentId}/subtasks/`);
  }

  async createSubtask(parentId: string, data: CreateTaskData): Promise<Task> {
    return apiClient.post<Task>(`/tasks/tasks/${parentId}/subtasks/`, data);
  }

  // Comments
  async getComments(taskId: string): Promise<TaskComment[]> {
    return apiClient.get<TaskComment[]>(`/tasks/tasks/${taskId}/comments/`);
  }

  async addComment(taskId: string, content: string): Promise<TaskComment> {
    return apiClient.post<TaskComment>(`/tasks/tasks/${taskId}/comments/`, { content });
  }

  async updateComment(taskId: string, commentId: string, content: string): Promise<TaskComment> {
    return apiClient.patch<TaskComment>(`/tasks/tasks/${taskId}/comments/${commentId}/`, { content });
  }

  async deleteComment(taskId: string, commentId: string): Promise<void> {
    return apiClient.delete(`/tasks/tasks/${taskId}/comments/${commentId}/`);
  }

  // Attachments
  async getAttachments(taskId: string): Promise<TaskAttachment[]> {
    return apiClient.get<TaskAttachment[]>(`/tasks/tasks/${taskId}/attachments/`);
  }

  async uploadAttachment(taskId: string, file: File): Promise<TaskAttachment> {
    return apiClient.uploadFile<TaskAttachment>(`/tasks/tasks/${taskId}/attachments/`, file);
  }

  async deleteAttachment(taskId: string, attachmentId: string): Promise<void> {
    return apiClient.delete(`/tasks/tasks/${taskId}/attachments/${attachmentId}/`);
  }

  // Bulk operations
  async bulkUpdateTasks(data: {
    tasks: UpdateTaskData[];
  }): Promise<Task[]> {
    return apiClient.post<Task[]>('/tasks/tasks/bulk_update/', data);
  }

  async bulkDeleteTasks(taskIds: string[]): Promise<void> {
    return apiClient.post('/tasks/tasks/bulk_delete/', { ids: taskIds });
  }

  // Task templates
  async getTaskTemplates(): Promise<any[]> {
    return apiClient.get('/tasks/templates/');
  }

  async createTaskFromTemplate(templateId: string, data: Partial<CreateTaskData>): Promise<Task> {
    return apiClient.post<Task>(`/tasks/templates/${templateId}/create/`, data);
  }

  // Time tracking integration
  async startTimer(taskId: string, data?: {
    description?: string;
    billable?: boolean;
    tags?: string[];
  }): Promise<any> {
    return apiClient.post(`/tasks/tasks/${taskId}/start_timer/`, data);
  }

  async stopTimer(taskId: string): Promise<any> {
    return apiClient.post(`/tasks/tasks/${taskId}/stop_timer/`);
  }

  // Reports and analytics
  async getTaskReport(filters: TaskFilters & {
    group_by?: 'status' | 'priority' | 'assignee' | 'project';
    date_field?: 'created_at' | 'due_date' | 'completed_at';
  }): Promise<any> {
    return apiClient.get('/tasks/reports/', filters);
  }

  async getProductivityMetrics(filters: {
    start_date: string;
    end_date: string;
    user?: string;
    project?: string;
  }): Promise<any> {
    return apiClient.get('/tasks/metrics/', filters);
  }

  // Search and filtering
  async searchTasks(query: string, filters?: TaskFilters): Promise<Task[]> {
    return apiClient.get<Task[]>('/tasks/search/', { q: query, ...filters });
  }

  async getMyTasks(filters?: TaskFilters): Promise<Task[]> {
    return apiClient.get<Task[]>('/tasks/my-tasks/', filters);
  }

  async getAssignedTasks(filters?: TaskFilters): Promise<Task[]> {
    return apiClient.get<Task[]>('/tasks/assigned/', filters);
  }

  async getReportedTasks(filters?: TaskFilters): Promise<Task[]> {
    return apiClient.get<Task[]>('/tasks/reported/', filters);
  }
}

// Create and export singleton instance
export const tasksService = new TasksService();
export default tasksService;