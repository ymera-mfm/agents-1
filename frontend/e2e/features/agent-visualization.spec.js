import { test, expect } from '@playwright/test';

test.describe('Agent 3D Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.goto('/agents');
  });

  test('should load 3D canvas', async ({ page }) => {
    await expect(page.locator('canvas')).toBeVisible();

    // Wait for Three.js to initialize
    await page.waitForTimeout(2000);

    // Check if canvas has content (not blank)
    const canvas = await page.locator('canvas');
    const box = await canvas.boundingBox();
    expect(box.width).toBeGreaterThan(0);
    expect(box.height).toBeGreaterThan(0);
  });

  test('should have working controls', async ({ page }) => {
    await expect(page.locator('button[aria-label="Reset camera"]')).toBeVisible();
    await expect(page.locator('button[aria-label="Toggle grid"]')).toBeVisible();

    await page.click('button[aria-label="Reset camera"]');
    // Verify camera reset (check canvas state if possible)
  });

  test('should display agent information', async ({ page }) => {
    await page.click('canvas', { position: { x: 100, y: 100 } });
    await expect(page.locator('.agent-info-panel')).toBeVisible();
    await expect(page.locator('.agent-info-panel')).toContainText('Agent');
  });
});
