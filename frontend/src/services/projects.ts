import apiClient from './api';

export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  start_date: string | null;
  end_date: string | null;
  due_date: string | null;
  budget: number | null;
  actual_cost: number | null;
  progress_percentage: number;
  color: string;
  organization: string;
  organization_name: string;
  manager: string | null;
  manager_name: string | null;
  team_members: ProjectMember[];
  tags: string[];
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ProjectMember {
  id: string;
  user: string;
  user_name: string;
  user_email: string;
  role: 'manager' | 'developer' | 'designer' | 'qa' | 'stakeholder';
  joined_at: string;
  is_active: boolean;
}

export interface CreateProjectData {
  name: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  start_date?: string;
  end_date?: string;
  due_date?: string;
  budget?: number;
  color?: string;
  organization: string;
  manager?: string;
  tags?: string[];
}

export interface UpdateProjectData extends Partial<CreateProjectData> {
  id: string;
  status?: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
}

export interface ProjectFilters {
  status?: string;
  priority?: string;
  organization?: string;
  manager?: string;
  start_date_after?: string;
  end_date_before?: string;
  tags?: string[];
  search?: string;
}

class ProjectsService {
  // Project CRUD operations
  async getProjects(filters?: ProjectFilters): Promise<Project[]> {
    return apiClient.get<Project[]>('/projects/projects/', filters);
  }

  async getProject(id: string): Promise<Project> {
    return apiClient.get<Project>(`/projects/projects/${id}/`);
  }

  async createProject(data: CreateProjectData): Promise<Project> {
    return apiClient.post<Project>('/projects/projects/', data);
  }

  async updateProject(data: UpdateProjectData): Promise<Project> {
    const { id, ...updateData } = data;
    return apiClient.patch<Project>(`/projects/projects/${id}/`, updateData);
  }

  async deleteProject(id: string): Promise<void> {
    return apiClient.delete(`/projects/projects/${id}/`);
  }

  // Project status operations
  async startProject(id: string): Promise<Project> {
    return apiClient.post<Project>(`/projects/projects/${id}/start/`);
  }

  async completeProject(id: string): Promise<Project> {
    return apiClient.post<Project>(`/projects/projects/${id}/complete/`);
  }

  async pauseProject(id: string): Promise<Project> {
    return apiClient.post<Project>(`/projects/projects/${id}/pause/`);
  }

  // Team management
  async getProjectMembers(projectId: string): Promise<ProjectMember[]> {
    return apiClient.get<ProjectMember[]>(`/projects/projects/${projectId}/members/`);
  }

  async addProjectMember(projectId: string, data: {
    user: string;
    role: 'manager' | 'developer' | 'designer' | 'qa' | 'stakeholder';
  }): Promise<ProjectMember> {
    return apiClient.post<ProjectMember>(`/projects/projects/${projectId}/members/`, data);
  }

  async updateProjectMember(projectId: string, memberId: string, data: {
    role?: 'manager' | 'developer' | 'designer' | 'qa' | 'stakeholder';
    is_active?: boolean;
  }): Promise<ProjectMember> {
    return apiClient.patch<ProjectMember>(`/projects/projects/${projectId}/members/${memberId}/`, data);
  }

  async removeProjectMember(projectId: string, memberId: string): Promise<void> {
    return apiClient.delete(`/projects/projects/${projectId}/members/${memberId}/`);
  }

  // Tasks integration
  async getProjectTasks(projectId: string, filters?: any): Promise<any[]> {
    return apiClient.get(`/projects/projects/${projectId}/tasks/`, filters);
  }

  async getProjectTimesheets(projectId: string, filters?: any): Promise<any[]> {
    return apiClient.get(`/projects/projects/${projectId}/timesheets/`, filters);
  }

  // Reports and analytics
  async getProjectReport(projectId: string, filters?: {
    start_date?: string;
    end_date?: string;
    include_tasks?: boolean;
    include_timesheets?: boolean;
  }): Promise<any> {
    return apiClient.get(`/projects/projects/${projectId}/report/`, filters);
  }

  async getProjectMetrics(projectId: string, filters?: {
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    return apiClient.get(`/projects/projects/${projectId}/metrics/`, filters);
  }

  async getProjectsOverview(filters?: {
    organization?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    return apiClient.get('/projects/overview/', filters);
  }

  // Bulk operations
  async bulkUpdateProjects(data: {
    projects: UpdateProjectData[];
  }): Promise<Project[]> {
    return apiClient.post<Project[]>('/projects/projects/bulk_update/', data);
  }

  async bulkDeleteProjects(projectIds: string[]): Promise<void> {
    return apiClient.post('/projects/projects/bulk_delete/', { ids: projectIds });
  }

  // Templates
  async getProjectTemplates(): Promise<any[]> {
    return apiClient.get('/projects/templates/');
  }

  async createProjectFromTemplate(templateId: string, data: Partial<CreateProjectData>): Promise<Project> {
    return apiClient.post<Project>(`/projects/templates/${templateId}/create/`, data);
  }

  // Search and filtering
  async searchProjects(query: string, filters?: ProjectFilters): Promise<Project[]> {
    return apiClient.get<Project[]>('/projects/search/', { q: query, ...filters });
  }

  async getMyProjects(filters?: ProjectFilters): Promise<Project[]> {
    return apiClient.get<Project[]>('/projects/my-projects/', filters);
  }

  async getManagedProjects(filters?: ProjectFilters): Promise<Project[]> {
    return apiClient.get<Project[]>('/projects/managed/', filters);
  }

  // Export functionality
  async exportProject(projectId: string, format: 'pdf' | 'csv' | 'xlsx'): Promise<Blob> {
    const response = await apiClient.get(`/projects/projects/${projectId}/export/?format=${format}`, undefined, {
      responseType: 'blob'
    });
    return response as any;
  }

  async exportProjectsReport(filters: ProjectFilters & { format: 'pdf' | 'csv' | 'xlsx' }): Promise<Blob> {
    const response = await apiClient.get('/projects/export/', filters, {
      responseType: 'blob'
    });
    return response as any;
  }
}

// Create and export singleton instance
export const projectsService = new ProjectsService();
export default projectsService;