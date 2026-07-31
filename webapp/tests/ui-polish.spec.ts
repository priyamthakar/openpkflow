import { expect, test } from '@playwright/test'

test('health badge recovers after a transient cold-start failure', async ({ page }) => {
  let calls = 0
  await page.route('**/health', async (route) => {
    calls += 1
    // First probe fails (Render cold start / network blip); later probes succeed.
    if (calls === 1) {
      await route.abort('failed')
      return
    }
    await route.fulfill({
      json: { status: 'ok', engine_version: '2.8.0' },
    })
  })

  await page.goto('/nca')
  await expect(page.getByText(/engine v2\.8\.0/)).toBeVisible({ timeout: 15_000 })
  expect(calls).toBeGreaterThanOrEqual(2)
})

test('EmptyResults placeholder appears before first NCA run', async ({ page }) => {
  await page.goto('/nca')
  await expect(page.getByText('No results yet')).toBeVisible()
  await expect(page.getByText('Ctrl+Enter to run').first()).toBeVisible()
})

test('EmptyResults placeholder appears before first BE run', async ({ page }) => {
  await page.goto('/be')
  await expect(page.getByText('No BE result yet')).toBeVisible()
  await expect(page.getByText('Ctrl+Enter to run').first()).toBeVisible()
})

test('EmptyResults placeholder appears before first dissolution comparison', async ({ page }) => {
  await page.goto('/dissolution')
  await expect(page.getByText('No comparison yet')).toBeVisible()
})
