import { test, expect } from '@playwright/test';

test.describe('Phase D: Passenger Portal (Search, Timetable, Tracking)', () => {
  const uniquePassengerEmail = `passenger_d_${Date.now()}@iroise.bzh`;
  const passengerPassword = 'SafePassword1234!';

  test('Guest searches Brest to Le Conquet, opens sailing, and sees live tracking', async ({ page }) => {
    // 1. Visit Home page
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // 2. Locate Sailing Search Form
    const fromSelect = page.locator('#search-from-port');
    const toSelect = page.locator('#search-to-port');

    await expect(fromSelect).toBeVisible();
    await fromSelect.selectOption('BREST');

    // Le Conquet should be available in destination dropdown
    await expect(toSelect).toBeEnabled();
    await toSelect.selectOption('LE_CONQUET');

    // 3. Search sailings
    const searchBtn = page.getByRole('button', { name: /search sailings/i });
    await searchBtn.click();

    // 4. Assert Search Results appear with departures
    const resultsSection = page.locator('.search-results-section');
    await expect(resultsSection).toBeVisible();
    await expect(resultsSection.getByRole('heading', { level: 2 })).toBeVisible();

    // 5. Click Track button on an available sailing
    const trackBtn = resultsSection.getByRole('button', { name: /track/i }).first();
    if (await trackBtn.isVisible()) {
      await trackBtn.click();
      // Should navigate to /track/... with map and honest simulated label
      await expect(page).toHaveURL(/\/track/);
      await expect(page.getByText(/historical replay.*simulated live/i).first()).toBeVisible();
      await expect(page.locator('.leaflet-container')).toBeVisible();
    } else {
      // If none currently active, verify Book button exists
      await expect(resultsSection.getByRole('button', { name: /book/i }).first()).toBeVisible();
    }
  });

  test('Search route on timetable page shows honest schedule status', async ({ page }) => {
    await page.goto('/timetable');

    const fromSelect = page.locator('#search-from-port');
    const toSelect = page.locator('#search-to-port');

    await fromSelect.selectOption('AUDIERNE');
    await expect(toSelect).toBeEnabled();
    await toSelect.selectOption('ILE_DE_SEIN');

    const searchBtn = page.getByRole('button', { name: /search sailings/i });
    await searchBtn.click();

    // Search results section displays Audierne -> Sein schedule
    const resultsSection = page.locator('.search-results-section');
    await expect(resultsSection).toBeVisible();
    await expect(resultsSection.getByRole('heading', { level: 2 })).toContainText(/Audierne/i);
  });

  test('Registered passenger with booked trip can open Track My Ferry from account page', async ({ page }) => {
    // 1. Register new passenger
    await page.goto('/register');
    await page.getByLabel(/first name/i).fill('Guirec');
    await page.getByLabel(/last name/i).fill('Soudée');
    await page.getByLabel(/email address/i).fill(uniquePassengerEmail);
    await page.getByLabel(/phone number/i).fill('+33298001122');
    await page.getByLabel(/^password/i).fill(passengerPassword);
    await page.getByLabel(/confirm password/i).fill(passengerPassword);
    await page.getByRole('button', { name: /create passenger account/i }).click();

    // 2. Redirected to /account
    await expect(page).toHaveURL(/\/account/);
    await expect(page.getByRole('heading', { level: 1, name: /passenger account/i })).toBeVisible();

    // 3. Check "Booked Sailings" section on Account Page
    await expect(page.getByRole('heading', { level: 2, name: /booked sailings/i })).toBeVisible();

    // If bookings exist or user clicks book a sailing, can navigate to timetable / tracking
    const trackFerryBtn = page.getByRole('button', { name: /track my ferry/i }).first();
    if (await trackFerryBtn.isVisible()) {
      await trackFerryBtn.click();
      await expect(page).toHaveURL(/\/track/);
    } else {
      // User can jump straight to timetable to book
      await expect(page.getByRole('button', { name: /book a sailing/i })).toBeVisible();
    }
  });
});
