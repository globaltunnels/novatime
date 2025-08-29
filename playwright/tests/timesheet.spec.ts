import { test, expect } from '@playwright/test';
import { TimesheetPage } from './pages/timesheetPage';

test.describe('Timesheet Management', () => {
  let timesheetPage: TimesheetPage;

  test.beforeEach(async ({ page }) => {
    // Assuming user is already logged in
    timesheetPage = new TimesheetPage(page);
    await timesheetPage.navigateTo('/timesheet');
    await timesheetPage.waitForTimesheetLoad();
  });

  test('should display timesheet page correctly', async () => {
    // Assert
    await expect(timesheetPage.weeklyTimesheetTitle).toBeVisible();
    // Check initial total hours (should be 0 or default value)
    const totalHours = await timesheetPage.getTotalHours();
    expect(totalHours).not.toBeNull();
  });

  test('should add a new timesheet entry', async () => {
    // Arrange
    const initialEntriesCount = await timesheetPage.getEntriesCount();
    
    // Act
    await timesheetPage.addTimesheetEntry(
      'Project Alpha',
      'Work on feature implementation',
      '8'
    );
    
    // Assert
    const finalEntriesCount = await timesheetPage.getEntriesCount();
    expect(finalEntriesCount).toBe(initialEntriesCount + 1);
    
    // Check that total hours have updated
    const totalHours = await timesheetPage.getTotalHours();
    expect(totalHours).toContain('8');
  });

  test('should submit timesheet', async () => {
    // Act
    await timesheetPage.submitTimesheet();
    
    // Assert
    // Add assertions based on submission behavior
    // This might involve checking for confirmation messages or status changes
  });
});