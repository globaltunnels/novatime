import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/loginPage';

test.describe('User Authentication', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.navigateTo('/login');
  });

  test('should successfully log in with valid credentials', async ({ page }) => {
    // Arrange
    const validUsername = 'testuser';
    const validPassword = 'correctpassword';

    // Act
    await loginPage.login(validUsername, validPassword);

    // Assert
    await expect(page).toHaveURL('/');
    // Add additional assertions based on successful login indicators
  });

  test('should show error message with invalid credentials', async () => {
    // Arrange
    const invalidUsername = 'invaliduser';
    const invalidPassword = 'wrongpassword';

    // Act
    await loginPage.login(invalidUsername, invalidPassword);

    // Assert
    await loginPage.waitForErrorMessage();
    // Add assertion for specific error message
  });

  test('should not log in with empty credentials', async ({ page }) => {
    // Act
    await loginPage.login('', '');

    // Assert
    await expect(page).not.toHaveURL('/');
    // Add assertion for validation errors
  });
});