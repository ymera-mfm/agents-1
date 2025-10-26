import { test, expect } from '@playwright/test';

test.describe('State Management', () => {
  test('should persist user preferences', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Change theme
    await page.click('button[aria-label="Toggle theme"]');

    // Reload page
    await page.reload();

    // Check theme persisted
    await expect(page.locator('html')).toHaveClass(/dark/);
  });

  test('should maintain state across navigation', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Navigate through pages
    await page.goto('/projects');
    await page.goto('/analytics');
    await page.goto('/dashboard');

    // Verify user still authenticated
    await expect(page.locator('nav')).toContainText('Logout');
  });
});
