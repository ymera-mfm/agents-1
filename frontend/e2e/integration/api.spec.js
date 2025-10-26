import { test, expect } from '@playwright/test';

test.describe('API Integration', () => {
  test('should fetch dashboard data', async ({ page }) => {
    // Mock API if needed
    await page.route('**/api/dashboard/stats', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          agents: 10,
          projects: 5,
          tasks: 25
        })
      });
    });

    await page.goto('/dashboard');

    await expect(page.locator('.agent-count')).toHaveText('10');
    await expect(page.locator('.project-count')).toHaveText('5');
    await expect(page.locator('.task-count')).toHaveText('25');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });

    await page.goto('/dashboard');

    await expect(page.locator('.error-banner')).toBeVisible();
    await expect(page.locator('.error-banner')).toContainText('Unable to load data');
  });

  test('should handle network timeout', async ({ page }) => {
    await page.route('**/api/**', route => route.abort());

    await page.goto('/dashboard');

    await expect(page.locator('.error-banner')).toBeVisible();
  });
});
