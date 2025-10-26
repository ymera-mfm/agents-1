import { test, expect } from '@playwright/test';

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.goto('/projects');
  });

  test('should create new project', async ({ page }) => {
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="name"]', 'Test Project');
    await page.fill('textarea[name="description"]', 'Test Description');
    await page.click('button[type="submit"]');

    await expect(page.locator('.success-message')).toBeVisible();
    await expect(page.locator('.project-card')).toContainText('Test Project');
  });

  test('should edit existing project', async ({ page }) => {
    await page.click('.project-card:first-child button[aria-label="Edit"]');
    await page.fill('input[name="name"]', 'Updated Project');
    await page.click('button[type="submit"]');

    await expect(page.locator('.success-message')).toBeVisible();
    await expect(page.locator('.project-card')).toContainText('Updated Project');
  });

  test('should delete project', async ({ page }) => {
    const initialCount = await page.locator('.project-card').count();

    await page.click('.project-card:first-child button[aria-label="Delete"]');
    await page.click('button:has-text("Confirm")');

    await expect(page.locator('.project-card')).toHaveCount(initialCount - 1);
  });
});
