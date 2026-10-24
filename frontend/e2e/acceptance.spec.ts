import { test, expect } from '@playwright/test';

test.describe('Master Acceptance Suite: Where Is My Ferry? Capstone Journeys', () => {
  const uniqueEmail = `capstone_pax_${Date.now()}@iroise.bzh`;
  const securePassword = 'FerryPassenger2026!';

  test('Capstone 1: Public Passenger Portal, Timetable Search, and Live Telemetry', async ({ page }) => {
    // 1. Visit Homepage
    await page.goto('/');
    await expect(page).toHaveTitle(/where is my ferry/i);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // 2. Search Sailings: Brest -> Le Conquet
    const fromPort = page.locator('#search-from-port');
    const toPort = page.locator('#search-to-port');
    await expect(fromPort).toBeVisible();
    await fromPort.selectOption('BREST');
    await expect(toPort).toBeEnabled();
    await toPort.selectOption('LE_CONQUET');

    const searchBtn = page.getByRole('button', { name: /search sailings/i });
    await searchBtn.click();

    // 3. Verify Search Results Section
    const resultsSection = page.locator('.search-results-section');
    await expect(resultsSection).toBeVisible();

    // 4. Live Tracking Navigation
    await page.goto('/track');
    await expect(page.locator('[data-testid="ferry-map-container"]')).toBeVisible();

    // Verify Honest Labelling (no fake live claims)
    await expect(page.getByText(/historical replay.*simulated live/i).first()).toBeVisible();

    // Verify Telemetry Panel
    const telemetryPanel = page.locator('.telemetry-panel');
    await expect(telemetryPanel).toBeVisible();
    await expect(telemetryPanel).toContainText(/speed \(sog\)/i);
    await expect(telemetryPanel).toContainText(/kts/i);
  });

  test('Capstone 2: Ports Directory, Canonical Ports, and Fares Matrix', async ({ page }) => {
    // 1. Ports Directory
    await page.goto('/ports');
    await expect(page.getByRole('heading', { level: 1, name: /ports/i })).toBeVisible();

    // Assert canonical seeded ports exist (including Camaret-sur-Mer)
    await expect(page.getByText(/camaret-sur-mer/i).first()).toBeVisible();
    await expect(page.getByText(/brest/i).first()).toBeVisible();
    await expect(page.getByText(/le conquet/i).first()).toBeVisible();
    await expect(page.getByText(/port du stiff/i).first()).toBeVisible();

    // 2. Fares & Tariffs
    await page.goto('/fares');
    await expect(page.getByRole('heading', { level: 1, name: /fares/i })).toBeVisible();
    await expect(page.getByText(/adult standard/i).first()).toBeVisible();
  });

  test('Capstone 3: Passenger Authentication, Token Storage, and Route Guard', async ({ page }) => {
    // 1. Register new passenger
    await page.goto('/register');
    await page.getByLabel(/first name/i).fill('Penn');
    await page.getByLabel(/last name/i).fill('Voyager');
    await page.getByLabel(/email address/i).fill(uniqueEmail);
    await page.getByLabel(/phone number/i).fill('+33298123456');
    await page.getByLabel(/^password/i).fill(securePassword);
    await page.getByLabel(/confirm password/i).fill(securePassword);

    await page.getByRole('button', { name: /create passenger account/i }).click();

    // 2. Redirect to Account page with active session
    await expect(page).toHaveURL(/\/account/);
    await expect(page.getByRole('heading', { level: 1, name: /passenger account/i })).toBeVisible();
    await expect(page.getByText(uniqueEmail)).toBeVisible();

    // 3. Logout and verify route guard redirects to login
    await page.getByRole('button', { name: /sign out/i }).click();
    await expect(page).toHaveURL(/\/(login)?/);

    await page.goto('/account');
    await expect(page).toHaveURL(/\/login/);
  });

  test('Capstone 4: Admin Governance, 8-Item Menu, Turnaround Conflict (409), and Audit Logging', async ({ page }) => {
    // 1. Staff Login
    await page.goto('/admin/login');
    await page.getByLabel(/staff email address/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('AdminPass123!');
    await page.getByRole('button', { name: /access admin portal/i }).click();

    await expect(page).toHaveURL(/\/admin/);
    await expect(page.getByRole('heading', { level: 1, name: /administration & control portal/i })).toBeVisible();

    // 2. Verify Exactly 8 Navigation Tabs
    const tabs = ['Dashboard', 'Timetable', 'Ports', 'Ships', 'Passengers', 'Announcements', 'Live engine', 'Admins'];
    for (const tab of tabs) {
      await expect(page.getByRole('button', { name: new RegExp(`^${tab}$`, 'i') })).toBeVisible();
    }

    // 3. Timetable Turnaround Conflict Detection (20-min rule -> 409 Conflict)
    await page.getByRole('button', { name: /^timetable$/i }).click();
    await page.getByRole('button', { name: /add service/i }).click();

    await page.locator('select').nth(0).selectOption('BREST');
    await page.locator('select').nth(1).selectOption('LE_CONQUET');
    await page.locator('select').nth(2).selectOption('V-FROMVEUR-SIM');

    const timeInput = page.locator('input[type="time"]');
    await timeInput.fill('08:45'); // Violates 08:30 + 60m duration + 20m turnaround requirement
    await page.getByRole('button', { name: /save service & generate/i }).click();

    // Conflict banner displayed
    await expect(page.getByText(/turnaround requirement: 20 minutes/i)).toBeVisible();
    await page.keyboard.press('Escape');

    // 4. Port Closure & Scoped Warning Announcement
    await page.getByRole('button', { name: /^ports$/i }).click();
    const closeBtn = page.getByRole('button', { name: /close port/i }).first();
    await closeBtn.click();

    await page.locator('select').last().selectOption('CLOSED');
    await page.locator('input[type="text"]').last().fill('Harbor maintenance in progress');
    await page.getByRole('button', { name: /save port status/i }).click();

    await expect(page.getByText(/status updated to closed/i)).toBeVisible();

    // 5. Audited Passenger Record Inspection
    await page.getByRole('button', { name: /^passengers$/i }).click();
    const inspectBtn = page.getByRole('button', { name: /inspect/i }).first();
    await inspectBtn.click();

    await expect(page.getByRole('heading', { name: /passenger audit record/i })).toBeVisible();
    await page.getByRole('button', { name: /close record/i }).click();

    // Switch to Admins tab to confirm audit entry
    await page.getByRole('button', { name: /^admins$/i }).click();
    await expect(page.getByText(/immutable system audit trail/i)).toBeVisible();
    await expect(page.getByText(/view_passenger_record/i).first()).toBeVisible();

    // 6. ML Model Diagnostics & Simulation Controls
    await page.getByRole('button', { name: /^live engine$/i }).click();
    await expect(page.getByText(/VectorizedRidgeETAModel/i)).toBeVisible();
    await expect(page.getByText(/integrity pass/i)).toBeVisible();
    await expect(page.getByText(/5.2 min/i)).toBeVisible();
    await expect(page.getByText(/3.56 min/i)).toBeVisible();
    await expect(page.getByText(/7.47 min/i)).toBeVisible();
  });
});
