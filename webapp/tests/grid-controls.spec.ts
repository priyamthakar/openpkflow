import { expect, test } from '@playwright/test'

test('paste grid supports range selection, bulk delete, fill down and clear', async ({ page }) => {
  await page.goto('/nca')
  await page.getByRole('radio', { name: 'Paste table' }).click()

  const status = page.getByText(/rows? ready for/)
  const before = Number((await status.innerText()).match(/^(\d+)/)?.[1])
  expect(before).toBeGreaterThan(3)

  await page.getByRole('button', { name: 'Select row 1', exact: true }).click()
  await page.getByRole('button', { name: 'Select row 3', exact: true }).click({ modifiers: ['Shift'] })
  await expect(page.getByRole('button', { name: 'Delete 3 selected' })).toBeVisible()
  await page.getByRole('button', { name: 'Delete 3 selected' }).click()
  await expect(status).toHaveText(new RegExp(`^${before - 3} rows ready for`))

  const firstHeader = await page.getByRole('grid').locator('thead th').nth(1).innerText()
  const above = page.getByRole('grid').getByLabel(`${firstHeader}, row 1`, { exact: true })
  const below = page.getByRole('grid').getByLabel(`${firstHeader}, row 2`, { exact: true })
  await above.fill('S99')
  await below.fill('')
  await below.press('ControlOrMeta+d')
  await expect(below).toHaveValue('S99')

  await page.getByRole('button', { name: 'Clear', exact: true }).click()
  await expect(status).toHaveText(/^1 row ready for/)
})
