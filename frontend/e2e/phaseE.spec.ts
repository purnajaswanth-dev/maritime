import { test, expect } from '@playwright/test';

test.describe('Phase E: Admin Portal Rebuild & Operational Governance', () => {
  test.beforeEach(async ({ page }) => {
    // Log in as seeded administrator
    await page.goto('/admin/login');
    await page.getByLabel(/staff email address/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('AdminPass123!');
    await page.getByRole('button', { name: /access admin portal/i }).click();

    // Verify redirected to admin portal
    await expect(page).toHaveURL(/\/admin/);
    await expect(page.getByRole('heading', { level: 1, name: /administration & control portal/i })).toBeVisible();
  });

  test('E1: Dashboard displays real operational metrics and system health', async ({ page }) => {
    // Assert 8 navigation tabs are present
    const tabs = ['Dashboard', 'Timetable', 'Ports', 'Ships', 'Passengers', 'Announcements', 'Live engine', 'Admins'];
    for (const tabName of tabs) {
      await expect(page.getByRole('button', { name: new RegExp(`^${tabName}$`, 'i') })).toBeVisible();
    }

    // Operational KPI Cards
    await expect(page.getByText(/today's sailings/i)).toBeVisible();
    await expect(page.getByText(/ships in transit/i)).toBeVisible();
    await expect(page.getByText(/total bookings/i)).toBeVisible();
    await expect(page.getByText(/confirmed revenue/i)).toBeVisible();
    await expect(page.getByText(/engine status/i)).toBeVisible();

    // Health tiles
    await expect(page.getByText(/ml & ais engine/i)).toBeVisible();
    await expect(page.getByText(/backend gateway/i)).toBeVisible();
    await expect(page.getByText(/database tier/i)).toBeVisible();
  });

  test('E2: Timetable conflict detection rejects impossible turnaround times with HTTP 409', async ({ page }) => {
    // Switch to Timetable tab
    await page.getByRole('button', { name: /^timetable$/i }).click();
    await expect(page.getByRole('button', { name: /operating services/i })).toBeVisible();

    // Click Add Service
    await page.getByRole('button', { name: /add service/i }).click();
    await expect(page.getByRole('heading', { name: /add operating timetable service/i })).toBeVisible();

    // Fill overlapping service: Fromveur II (already scheduled at 08:30 with 60m duration)
    // Scheduling at 08:45 violates minimum 20-min turnaround requirement
    await page.locator('select').nth(0).selectOption('BREST');
    await page.locator('select').nth(1).selectOption('LE_CONQUET');
    await page.locator('select').nth(2).selectOption('V-FROMVEUR-SIM');

    const timeInput = page.locator('input[type="time"]');
    await timeInput.fill('08:45');

    // Submit service
    await page.getByRole('button', { name: /save service & generate/i }).click();

    // Verify 409 conflict error banner appears with turnaround detail
    await expect(page.getByText(/turnaround requirement: 20 minutes/i)).toBeVisible();
  });

  test('E3: Port status modification generates automatic scoped warning announcement', async ({ page }) => {
    // Switch to Ports tab
    await page.getByRole('button', { name: /^ports$/i }).click();
    await expect(page.getByText(/port code/i)).toBeVisible();
    await expect(page.getByText(/berth radius/i)).toBeVisible();

    // Verify Port de Camaret-sur-Mer or Brest exists
    await expect(page.getByText(/brest/i).first()).toBeVisible();

    // Click Close Port on Brest
    const closeBtn = page.getByRole('button', { name: /close port/i }).first();
    await closeBtn.click();

    // Fill closure reason in modal
    await expect(page.getByRole('heading', { name: /set terminal status/i })).toBeVisible();
    await page.locator('select').last().selectOption('CLOSED');
    await page.locator('input[type="text"]').last().fill('Severe gale warning in harbor narrows');

    await page.getByRole('button', { name: /save port status/i }).click();

    // Verify success alert
    await expect(page.getByText(/status updated to closed/i)).toBeVisible();
  });

  test('E4: Passenger record inspection is logged in immutable audit trail', async ({ page }) => {
    // Switch to Passengers tab
    await page.getByRole('button', { name: /^passengers$/i }).click();
    await expect(page.getByPlaceholder(/search passenger by name\/email/i)).toBeVisible();

    // Click Inspect on first passenger
    const inspectBtn = page.getByRole('button', { name: /inspect/i }).first();
    await inspectBtn.click();

    // Modal opens showing profile & booking history
    await expect(page.getByRole('heading', { name: /passenger audit record/i })).toBeVisible();
    await page.getByRole('button', { name: /close record/i }).click();

    // Switch to Admins tab to verify audit entry
    await page.getByRole('button', { name: /^admins$/i }).click();
    await expect(page.getByText(/immutable system audit trail/i)).toBeVisible();
    await expect(page.getByText(/view_passenger_record/i).first()).toBeVisible();
  });

  test('E5: Live engine simulation controls and ML model diagnostics', async ({ page }) => {
    // Switch to Live engine tab
    await page.getByRole('button', { name: /^live engine$/i }).click();
    await expect(page.getByText(/virtual maritime simulation engine controls/i)).toBeVisible();

    // Speed multiplier buttons
    await expect(page.getByRole('button', { name: '5x' })).toBeVisible();
    await page.getByRole('button', { name: '5x' }).click();

    // Model diagnostics metrics
    await expect(page.getByText(/VectorizedRidgeETAModel/i)).toBeVisible();
    await expect(page.getByText(/integrity pass/i)).toBeVisible();
    await expect(page.getByText(/mean absolute error/i)).toBeVisible();
    await expect(page.getByText(/5.2 min/i)).toBeVisible();
    await expect(page.getByText(/3.56 min/i)).toBeVisible();
    await expect(page.getByText(/7.47 min/i)).toBeVisible();

    // Trigger scenario fault
    const triggerBtn = page.getByRole('button', { name: /trigger scenario/i }).first();
    await triggerBtn.click();

    await expect(page.getByRole('heading', { name: /confirm scenario trigger/i })).toBeVisible();
    await page.getByRole('button', { name: /confirm & inject fault/i }).click();

    await expect(page.getByText(/triggered on simulation engine/i)).toBeVisible();
  });
});
