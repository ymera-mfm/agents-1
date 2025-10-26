import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should display dashboard components', async ({ page }) => {
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('.stats-card')).toHaveCount(4);
  });

  test('should have working navigation', async ({ page }) => {
    await page.click('a[href="/projects"]');
    await expect(page).toHaveURL('/projects');

    await page.click('a[href="/analytics"]');
    await expect(page).toHaveURL('/analytics');
  });

  test('should display data correctly', async ({ page }) => {
    await expect(page.locator('.agent-count')).not.toBeEmpty();
    await expect(page.locator('.project-count')).not.toBeEmpty();
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('button[aria-label="Toggle menu"]')).toBeVisible();

    await page.click('button[aria-label="Toggle menu"]');
    await expect(page.locator('.mobile-menu')).toBeVisible();
  });
});
