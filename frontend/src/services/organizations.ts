import apiClient from './api';

export interface Organization {
  id: string;
  name: string;
  description: string;
  domain: string | null;
  logo_url: string | null;
  website: string | null;
  address: string | null;
  phone: string | null;
  industry: string | null;
  size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  timezone: string;
  currency: string;
  is_active: boolean;
  owner: string;
  owner_name: string;
  created_at: string;
  updated_at: string;
  member_count: number;
  project_count: number;
}

export interface OrganizationMember {
  id: string;
  user: string;
  user_name: string;
  user_email: string;
  role: 'owner' | 'admin' | 'manager' | 'member';
  joined_at: string;
  invited_by: string | null;
  invited_by_name: string | null;
  is_active: boolean;
}

export interface CreateOrganizationData {
  name: string;
  description?: string;
  domain?: string;
  website?: string;
  address?: string;
  phone?: string;
  industry?: string;
  size?: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  timezone?: string;
  currency?: string;
}

export interface UpdateOrganizationData extends Partial<CreateOrganizationData> {
  id: string;
}

export interface OrganizationInvitation {
  id: string;
  email: string;
  role: 'admin' | 'manager' | 'member';
  invited_by: string;
  invited_by_name: string;
  invited_at: string;
  expires_at: string;
  is_accepted: boolean;
  accepted_at: string | null;
}

class OrganizationsService {
  // Organization CRUD operations
  async getOrganizations(): Promise<Organization[]> {
    return apiClient.get<Organization[]>('/organizations/organizations/');
  }

  async getOrganization(id: string): Promise<Organization> {
    return apiClient.get<Organization>(`/organizations/organizations/${id}/`);
  }

  async createOrganization(data: CreateOrganizationData): Promise<Organization> {
    return apiClient.post<Organization>('/organizations/organizations/', data);
  }

  async updateOrganization(data: UpdateOrganizationData): Promise<Organization> {
    const { id, ...updateData } = data;
    return apiClient.patch<Organization>(`/organizations/organizations/${id}/`, updateData);
  }

  async deleteOrganization(id: string): Promise<void> {
    return apiClient.delete(`/organizations/organizations/${id}/`);
  }

  // Member management
  async getOrganizationMembers(orgId: string): Promise<OrganizationMember[]> {
    return apiClient.get<OrganizationMember[]>(`/organizations/organizations/${orgId}/members/`);
  }

  async addOrganizationMember(orgId: string, data: {
    email: string;
    role: 'admin' | 'manager' | 'member';
    send_invitation?: boolean;
  }): Promise<OrganizationMember> {
    return apiClient.post<OrganizationMember>(`/organizations/organizations/${orgId}/members/`, data);
  }

  async updateOrganizationMember(orgId: string, memberId: string, data: {
    role?: 'owner' | 'admin' | 'manager' | 'member';
    is_active?: boolean;
  }): Promise<OrganizationMember> {
    return apiClient.patch<OrganizationMember>(`/organizations/organizations/${orgId}/members/${memberId}/`, data);
  }

  async removeOrganizationMember(orgId: string, memberId: string): Promise<void> {
    return apiClient.delete(`/organizations/organizations/${orgId}/members/${memberId}/`);
  }

  // Invitations
  async getPendingInvitations(orgId: string): Promise<OrganizationInvitation[]> {
    return apiClient.get<OrganizationInvitation[]>(`/organizations/organizations/${orgId}/invitations/`);
  }

  async resendInvitation(orgId: string, invitationId: string): Promise<void> {
    return apiClient.post(`/organizations/organizations/${orgId}/invitations/${invitationId}/resend/`);
  }

  async cancelInvitation(orgId: string, invitationId: string): Promise<void> {
    return apiClient.delete(`/organizations/organizations/${orgId}/invitations/${invitationId}/`);
  }

  async acceptInvitation(token: string): Promise<OrganizationMember> {
    return apiClient.post<OrganizationMember>('/organizations/invitations/accept/', { token });
  }

  async declineInvitation(token: string): Promise<void> {
    return apiClient.post('/organizations/invitations/decline/', { token });
  }

  // Current user's organizations
  async getMyOrganizations(): Promise<Organization[]> {
    return apiClient.get<Organization[]>('/organizations/my-organizations/');
  }

  async switchOrganization(orgId: string): Promise<void> {
    return apiClient.post('/organizations/switch/', { organization: orgId });
  }

  // Organization settings
  async updateOrganizationSettings(orgId: string, settings: {
    timezone?: string;
    currency?: string;
    working_hours_start?: string;
    working_hours_end?: string;
    working_days?: number[];
    allow_overtime?: boolean;
    require_timesheet_approval?: boolean;
    default_billable_rate?: number;
  }): Promise<any> {
    return apiClient.patch(`/organizations/organizations/${orgId}/settings/`, settings);
  }

  async getOrganizationSettings(orgId: string): Promise<any> {
    return apiClient.get(`/organizations/organizations/${orgId}/settings/`);
  }

  // Billing and subscription (if applicable)
  async getOrganizationBilling(orgId: string): Promise<any> {
    return apiClient.get(`/organizations/organizations/${orgId}/billing/`);
  }

  async updateBillingInfo(orgId: string, data: any): Promise<any> {
    return apiClient.patch(`/organizations/organizations/${orgId}/billing/`, data);
  }

  // Reports and analytics
  async getOrganizationReport(orgId: string, filters?: {
    start_date?: string;
    end_date?: string;
    include_projects?: boolean;
    include_users?: boolean;
  }): Promise<any> {
    return apiClient.get(`/organizations/organizations/${orgId}/report/`, filters);
  }

  async getOrganizationMetrics(orgId: string, filters?: {
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    return apiClient.get(`/organizations/organizations/${orgId}/metrics/`, filters);
  }

  // Bulk operations
  async bulkInviteMembers(orgId: string, invitations: Array<{
    email: string;
    role: 'admin' | 'manager' | 'member';
  }>): Promise<OrganizationInvitation[]> {
    return apiClient.post<OrganizationInvitation[]>(`/organizations/organizations/${orgId}/bulk-invite/`, {
      invitations
    });
  }

  // Search
  async searchOrganizations(query: string): Promise<Organization[]> {
    return apiClient.get<Organization[]>('/organizations/search/', { q: query });
  }

  // Export functionality
  async exportOrganizationData(orgId: string, format: 'pdf' | 'csv' | 'xlsx'): Promise<Blob> {
    const response = await apiClient.get(`/organizations/organizations/${orgId}/export/?format=${format}`, undefined, {
      responseType: 'blob'
    });
    return response as any;
  }

  async exportMembers(orgId: string, format: 'csv' | 'xlsx'): Promise<Blob> {
    const response = await apiClient.get(`/organizations/organizations/${orgId}/members/export/?format=${format}`, undefined, {
      responseType: 'blob'
    });
    return response as any;
  }
}

// Create and export singleton instance
export const organizationsService = new OrganizationsService();
export default organizationsService;