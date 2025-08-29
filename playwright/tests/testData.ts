// Test data factory for consistent test data across tests

export const testUsers = {
  admin: {
    username: 'admin',
    password: 'adminpassword',
    email: 'admin@novatime.com'
  },
  manager: {
    username: 'manager',
    password: 'managerpassword',
    email: 'manager@novatime.com'
  },
  employee: {
    username: 'employee',
    password: 'employeepassword',
    email: 'employee@novatime.com'
  }
};

export const testProjects = {
  alpha: {
    name: 'Project Alpha',
    description: 'Test project for Alpha features',
    status: 'active'
  },
  beta: {
    name: 'Project Beta',
    description: 'Test project for Beta features',
    status: 'active'
  }
};

export const testTasks = {
  frontend: {
    title: 'Frontend Development',
    description: 'Implement UI components',
    priority: 'high'
  },
  backend: {
    title: 'Backend Development',
    description: 'Implement API endpoints',
    priority: 'high'
  }
};

export const testTimesheetEntries = {
  monday: {
    project: 'Project Alpha',
    description: 'Work on frontend components',
    hours: 8,
    date: '2023-08-21'
  },
  tuesday: {
    project: 'Project Beta',
    description: 'Backend API development',
    hours: 8,
    date: '2023-08-22'
  }
};