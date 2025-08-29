import { Page, Locator } from '@playwright/test';

export class BasePage {
  readonly page: Page;
  
  constructor(page: Page) {
    this.page = page;
  }
  
  async navigateTo(path: string = '/') {
    await this.page.goto(path);
  }
  
  async clickElement(locator: Locator) {
    await locator.click();
  }
  
  async fillInput(locator: Locator, value: string) {
    await locator.fill(value);
  }
  
  async waitForElementVisible(locator: Locator, timeout: number = 30000) {
    await locator.waitFor({ state: 'visible', timeout });
  }
  
  async waitForElementHidden(locator: Locator, timeout: number = 30000) {
    await locator.waitFor({ state: 'hidden', timeout });
  }
}