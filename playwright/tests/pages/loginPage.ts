import { Page, Locator } from '@playwright/test';
import { BasePage } from './basePage';

export class LoginPage extends BasePage {
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  
  constructor(page: Page) {
    super(page);
    this.usernameInput = page.getByPlaceholder('Username or email');
    this.passwordInput = page.getByPlaceholder('Password');
    this.loginButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.locator('.error-message');
  }
  
  async login(username: string, password: string) {
    await this.fillInput(this.usernameInput, username);
    await this.fillInput(this.passwordInput, password);
    await this.clickElement(this.loginButton);
  }
  
  async waitForErrorMessage() {
    await this.waitForElementVisible(this.errorMessage);
  }
}