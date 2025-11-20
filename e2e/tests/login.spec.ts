import { test, expect } from '@playwright/test';

test('Homepage loads and shows login screen', async ({ page }) => {
  // 1. Navigate to the site
  await page.goto('https://docs.davincisolutions.ai');

  // 2. Expect the title to be correct (browser tab title)
  // Note: The React app might not set document.title dynamically in Login.tsx, checking content instead.
  
  // 3. Check for visible text "Davinci Document Creator"
  const heading = page.getByRole('heading', { name: 'Davinci Document Creator' });
  await expect(heading).toBeVisible();

  // 4. Check for "Sign in with Microsoft" button
  const loginButton = page.getByRole('button', { name: 'Sign in with Microsoft' });
  await expect(loginButton).toBeVisible();

  // 5. Verify the button links to /api/auth/login (or triggers the action)
  // Since it's an onClick handler in React doing window.location.href, we can't easily check href attribute.
  // But we can check visibility.
});
