import { test, expect } from '@playwright/test';

async function dnd(page, sourceTestId: string, targetSelector: string) {
  const src = page.getByTestId(sourceTestId);
  const tgt = page.locator(targetSelector).first();
  const srcBox = await src.boundingBox();
  const tgtBox = await tgt.boundingBox();
  if (!srcBox || !tgtBox) throw new Error('missing boxes');
  await page.mouse.move(srcBox.x + srcBox.width/2, srcBox.y + srcBox.height/2);
  await page.mouse.down();
  await page.mouse.move(tgtBox.x + tgtBox.width/2, tgtBox.y + tgtBox.height/2);
  await page.mouse.up();
}

test('drag agent node, open inspector, change mode', async ({ page }) => {
  await page.goto('/');
  await dnd(page, 'palette-agent', '.react-flow__pane');
  // Click a node header to focus and then double click to open inspector
  await page.getByTestId('node-header').first().dblclick();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Mode').selectOption('workflow');
  // Save by closing
  await page.getByLabel('Close').click();
  await expect(page.getByRole('dialog')).toBeHidden();
});

test('export JSON button exists', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('export-json')).toBeVisible();
});
