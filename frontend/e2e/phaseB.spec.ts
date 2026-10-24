import { test, expect } from '@playwright/test';

test.describe('Phase B: Passenger & Admin Authentication E2E', () => {
  const uniquePassengerEmail = `passenger_${Date.now()}@iroise.bzh`;
  const passengerPassword = 'SafePassword1234!';

  test('Full authentication flow: registration, session persistence, unauthorized guard, and admin portal access', async ({ page, context }) => {
    // 1. Passenger Registration
    await page.goto('/register');
    await expect(page.getByRole('heading', { level: 1, name: /passenger registration/i })).toBeVisible();

    await page.getByLabel(/first name/i).fill('Ronan');
    await page.getByLabel(/last name/i).fill('Le Gall');
    await page.getByLabel(/email address/i).fill(uniquePassengerEmail);
    await page.getByLabel(/phone number/i).fill('+33298123456');
    await page.getByLabel(/^password/i).fill(passengerPassword);
    await page.getByLabel(/confirm password/i).fill(passengerPassword);

    await page.getByRole('button', { name: /create passenger account/i }).click();

    // Should redirect to /account
    await expect(page).toHaveURL(/\/account/);
    await expect(page.getByRole('heading', { level: 1, name: /passenger account/i })).toBeVisible();
    await expect(page.getByText(uniquePassengerEmail)).toBeVisible();

    // 2. Log out (protected /account sends logged-out user to /login)
    await page.getByRole('button', { name: /sign out/i }).click();
    await expect(page).toHaveURL(/\/login/);

    // 3. Log in
    await page.goto('/login');
    await page.getByLabel(/email address/i).fill(uniquePassengerEmail);
    await page.getByLabel(/password/i).fill(passengerPassword);
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page).toHaveURL(/\/account/);
    await expect(page.getByText(uniquePassengerEmail)).toBeVisible();

    // 4. Reload page (assert session persistence via refresh token / cookie)
    await page.reload();
    await expect(page).toHaveURL(/\/account/);
    await expect(page.getByText(uniquePassengerEmail)).toBeVisible();

    // 5. Try accessing /admin as passenger -> redirected to /unauthorized
    await page.goto('/admin');
    await expect(page).toHaveURL(/\/unauthorized/);
    await expect(page.getByRole('heading', { level: 1, name: /access restricted/i })).toBeVisible();

    // 6. Log out from unauthorized page
    await page.getByRole('button', { name: /sign in with another account/i }).click();
    await expect(page).toHaveURL(/\/admin\/login/);

    // 7. Log in as seeded administrator
    await page.getByLabel(/staff email address/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('AdminPass123!');
    await page.getByRole('button', { name: /access admin portal/i }).click();

    // 8. Reaches admin portal
    await expect(page).toHaveURL(/\/admin/);
    await expect(page.getByRole('heading', { level: 1, name: /administration & control portal/i })).toBeVisible();
  });
});
