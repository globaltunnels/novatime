import { Page, Locator } from '@playwright/test';
import { BasePage } from './basePage';

export class ApprovalsPage extends BasePage {
  readonly approvalsTitle: Locator;
  readonly pendingApprovalsList: Locator;
  readonly approveButtons: Locator;
  readonly rejectButtons: Locator;
  readonly filterSelect: Locator;
  
  constructor(page: Page) {
    super(page);
    this.approvalsTitle = page.getByText('Timesheet Approvals');
    this.pendingApprovalsList = page.locator('tbody tr');
    this.approveButtons = page.getByRole('button', { name: 'Approve' });
    this.rejectButtons = page.getByRole('button', { name: 'Reject' });
    this.filterSelect = page.locator('select');
  }
  
  async waitForApprovalsLoad() {
    await this.waitForElementVisible(this.approvalsTitle);
  }
  
  async getPendingApprovalsCount(): Promise<number> {
    return await this.pendingApprovalsList.count();
  }
  
  async approveTimesheet(index: number = 0) {
    const approveButton = this.approveButtons.nth(index);
    await this.clickElement(approveButton);
  }
  
  async rejectTimesheet(index: number = 0) {
    const rejectButton = this.rejectButtons.nth(index);
    await this.clickElement(rejectButton);
  }
  
  async filterByStatus(status: string) {
    await this.filterSelect.selectOption(status);
  }
}