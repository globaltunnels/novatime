import { Page, Locator } from '@playwright/test';
import { BasePage } from './basePage';

export class ProjectsPage extends BasePage {
  readonly projectsTitle: Locator;
  readonly createProjectButton: Locator;
  readonly projectList: Locator;
  readonly searchInput: Locator;
  
  constructor(page: Page) {
    super(page);
    this.projectsTitle = page.getByText('Projects');
    this.createProjectButton = page.getByRole('button', { name: 'Create Project' });
    this.projectList = page.locator('tbody tr');
    this.searchInput = page.getByPlaceholder('Search projects...');
  }
  
  async waitForProjectsLoad() {
    await this.waitForElementVisible(this.projectsTitle);
  }
  
  async createNewProject() {
    await this.clickElement(this.createProjectButton);
  }
  
  async searchProjects(query: string) {
    await this.fillInput(this.searchInput, query);
  }
  
  async getProjectsCount(): Promise<number> {
    return await this.projectList.count();
  }
}