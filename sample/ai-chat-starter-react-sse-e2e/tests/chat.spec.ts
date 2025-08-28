import { test, expect } from '@playwright/test';

test('can stream a response and stop it', async ({ page }) => {
  await page.goto('/');
  await page.getByTestId('composer-input').click();
  await page.keyboard.type('Write a fibonacci in python');
  await page.getByTestId('composer-send').click();

  // Should show assistant bubble and begin streaming text
  await expect(page.getByTestId('chat-message').nth(1)).toBeVisible();
  await page.waitForTimeout(500); // let stream start
  const before = await page.getByTestId('chat-message').nth(1).textContent();

  // Stop should be visible during stream
  await expect(page.getByTestId('composer-stop')).toBeVisible();
  await page.getByTestId('composer-stop').click();

  // After a brief wait, text should remain and stop button hide
  await page.waitForTimeout(200);
  await expect(page.getByTestId('composer-stop')).toHaveClass(/hidden/);

  const after = await page.getByTestId('chat-message').nth(1).textContent();
  expect(after && before).toBeTruthy();
});

test('scroll-to-bottom FAB appears when scrolled up', async ({ page }) => {
  await page.goto('/');
  // spam a few messages to create scroll
  for (let i = 0; i < 5; i++) {
    await page.getByTestId('composer-input').click();
    await page.keyboard.type('Ping ' + i);
    await page.getByTestId('composer-send').click();
    await page.waitForTimeout(200);
  }
  const messages = page.locator('[role="log"]');
  await messages.evaluate(el => el.scrollTop = 0);
  await expect(page.getByTestId('scroll-fab')).not.toHaveClass(/hidden/);
});
