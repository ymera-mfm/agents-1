import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('dashboard should match screenshot', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      maxDiffPixels: 100
    });
  });

  test('mobile view should match screenshot', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    await expect(page).toHaveScreenshot('dashboard-mobile.png', {
      fullPage: true
    });
  });
});
