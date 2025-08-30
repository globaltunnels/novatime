// API Client
export { default as apiClient } from './api';
export type { ApiResponse, ApiError } from './api';

// Authentication Service
export { default as authService } from './auth';
export type {
  User,
  LoginCredentials,
  RegisterData,
  AuthTokens,
  LoginResponse
} from './auth';

// Timesheets Service
export { default as timesheetsService } from './timesheets';
export type {
  TimesheetEntry,
  Timesheet,
  TimesheetApproval,
  CreateTimesheetEntryData,
  UpdateTimesheetEntryData,
  TimesheetFilters
} from './timesheets';

// Tasks Service
export { default as tasksService } from './tasks';
export type {
  Task,
  TaskAttachment,
  TaskComment,
  CreateTaskData,
  UpdateTaskData,
  TaskFilters
} from './tasks';

// Projects Service
export { default as projectsService } from './projects';
export type {
  Project,
  ProjectMember,
  CreateProjectData,
  UpdateProjectData,
  ProjectFilters
} from './projects';

// Organizations Service
export { default as organizationsService } from './organizations';
export type {
  Organization,
  OrganizationMember,
  CreateOrganizationData,
  UpdateOrganizationData,
  OrganizationInvitation
} from './organizations';

// Re-export all services as a single object for convenience
export const services = {
  auth: authService,
  timesheets: timesheetsService,
  tasks: tasksService,
  projects: projectsService,
  organizations: organizationsService,
  api: apiClient,
};