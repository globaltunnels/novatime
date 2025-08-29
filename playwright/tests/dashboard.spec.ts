import { test, expect } from '@playwright/test';
import { DashboardPage } from './pages/dashboardPage';

test.describe('Dashboard', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    // Assuming user is already logged in
    dashboardPage = new DashboardPage(page);
    await dashboardPage.navigateTo('/');
    await dashboardPage.waitForDashboardLoad();
  });

  test('should display dashboard elements correctly', async () => {
    // Assert
    await expect(dashboardPage.headerTitle).toBeVisible();
    await expect(dashboardPage.startTimerButton).toBeVisible();
    await expect(dashboardPage.addTaskButton).toBeVisible();
    await expect(dashboardPage.userAvatar).toBeVisible();
    
    // Check notification badge
    const notificationCount = await dashboardPage.getNotificationCount();
    expect(notificationCount).toEqual('3');
    
    // Check sidebar items
    const sidebarItemsCount = await dashboardPage.getSidebarItemsCount();
    expect(sidebarItemsCount).toBeGreaterThan(0);
  });

  test('should navigate to different sections via sidebar', async () => {
    // Act & Assert
    await dashboardPage.navigateToSection('Timesheet');
    await expect(dashboardPage.page).toHaveURL(/.*timesheet/);
    
    // Navigate back to dashboard
    await dashboardPage.navigateTo('/');
    await dashboardPage.waitForDashboardLoad();
    
    await dashboardPage.navigateToSection('Projects');
    await expect(dashboardPage.page).toHaveURL(/.*projects/);
  });

  test('should start timer when start timer button is clicked', async () => {
    // Act
    await dashboardPage.clickStartTimer();
    
    // Assert
    // Add assertions based on timer start behavior
  });
});