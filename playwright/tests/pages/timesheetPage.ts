import { Page, Locator } from '@playwright/test';
import { BasePage } from './basePage';

export class TimesheetPage extends BasePage {
  readonly weeklyTimesheetTitle: Locator;
  readonly projectNameInput: Locator;
  readonly taskDescriptionInput: Locator;
  readonly hoursInput: Locator;
  readonly saveEntryButton: Locator;
  readonly submitTimesheetButton: Locator;
  readonly timesheetEntries: Locator;
  readonly totalHours: Locator;
  
  constructor(page: Page) {
    super(page);
    this.weeklyTimesheetTitle = page.getByText('Weekly Timesheet');
    this.projectNameInput = page.getByPlaceholder('Project name');
    this.taskDescriptionInput = page.getByPlaceholder('What did you work on?');
    this.hoursInput = page.getByPlaceholder('Hours');
    this.saveEntryButton = page.getByRole('button', { name: 'Save Entry' });
    this.submitTimesheetButton = page.getByRole('button', { name: 'Submit Timesheet' });
    this.timesheetEntries = page.locator('tbody tr');
    this.totalHours = page.locator('.text-3xl.font-bold');
  }
  
  async waitForTimesheetLoad() {
    await this.waitForElementVisible(this.weeklyTimesheetTitle);
  }
  
  async addTimesheetEntry(project: string, description: string, hours: string) {
    await this.fillInput(this.projectNameInput, project);
    await this.fillInput(this.taskDescriptionInput, description);
    await this.fillInput(this.hoursInput, hours);
    await this.clickElement(this.saveEntryButton);
  }
  
  async submitTimesheet() {
    await this.clickElement(this.submitTimesheetButton);
  }
  
  async getEntriesCount(): Promise<number> {
    return await this.timesheetEntries.count();
  }
  
  async getTotalHours(): Promise<string | null> {
    return await this.totalHours.textContent();
  }
}