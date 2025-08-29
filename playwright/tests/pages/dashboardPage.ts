import { Page, Locator } from '@playwright/test';
import { BasePage } from './basePage';

export class DashboardPage extends BasePage {
  readonly headerTitle: Locator;
  readonly startTimerButton: Locator;
  readonly addTaskButton: Locator;
  readonly notificationBadge: Locator;
  readonly userAvatar: Locator;
  readonly sidebar: Locator;
  readonly sidebarItems: Locator;
  
  constructor(page: Page) {
    super(page);
    this.headerTitle = page.getByText('Today - Wednesday, Aug 28');
    this.startTimerButton = page.getByText('⏱️ Start Timer');
    this.addTaskButton = page.getByText('➕ Add Task');
    this.notificationBadge = page.locator('.relative').locator('div').nth(1);
    this.userAvatar = page.locator('.w-8.h-8');
    this.sidebar = page.locator('.border-r');
    this.sidebarItems = page.locator('.border-r a');
  }
  
  async waitForDashboardLoad() {
    await this.waitForElementVisible(this.headerTitle);
  }
  
  async clickStartTimer() {
    await this.clickElement(this.startTimerButton);
  }
  
  async clickAddTask() {
    await this.clickElement(this.addTaskButton);
  }
  
  async getNotificationCount(): Promise<string | null> {
    return await this.notificationBadge.textContent();
  }
  
  async getSidebarItemsCount(): Promise<number> {
    return await this.sidebarItems.count();
  }
  
  async navigateToSection(sectionName: string) {
    const sectionLink = this.page.getByRole('link', { name: sectionName });
    await this.clickElement(sectionLink);
  }
}