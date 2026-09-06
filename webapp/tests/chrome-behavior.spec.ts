import { expect, test } from '@playwright/test'

const disclaimer =
  'This report was generated using OpenPKFlow (open-source). Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.'

async function mockTwoSeriesDissolution(page: import('@playwright/test').Page) {
  await page.route('**/api/dissolution/formulations', async (route) => {
    await route.fulfill({ json: { formulations: ['Reference', 'Test'] } })
  })
  await page.route('**/api/dissolution/compare', async (route) => {
    await route.fulfill({
      json: {
        reference_label: 'Reference',
        test_label: 'Test',
        f1_value: 1.2,
        f2_value: 86.4,
        similar: true,
        n_timepoints: 4,
        time_points: [5, 10, 15, 30],
        reference_mean: [29, 49, 68, 92],
        test_mean: [26.5, 48, 67, 91],
        warnings: [],
        disclaimer,
      },
    })
  })
}

async function runTwoSeriesDissolution(page: import('@playwright/test').Page) {
  await mockTwoSeriesDissolution(page)
  await page.goto('/dissolution')
  await page.getByRole('radio', { name: 'Paste table' }).click()
  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page.getByText('86.400')).toBeVisible()
}

test('PKChart legend series toggle hides and restores the series', async ({ page }) => {
  await runTwoSeriesDissolution(page)

  const legendItem = page.locator('.recharts-legend-item', { hasText: 'Test' })
  const testCurve = page.locator('path.recharts-line-curve[stroke="#3dd68c"]')
  const referenceCurve = page.locator('path.recharts-line-curve[stroke="#5e6ad2"]')

  await expect(legendItem).toBeVisible()
  await expect(testCurve).toHaveCount(1)
  await expect(referenceCurve).toHaveCount(1)

  await legendItem.click()
  await expect(testCurve).toHaveCount(0)
  await expect(referenceCurve).toHaveCount(1)

  await legendItem.click()
  await expect(testCurve).toHaveCount(1)
  await expect(referenceCurve).toHaveCount(1)
})

test('PKChart PNG export downloads pk_chart.png', async ({ page }) => {
  await runTwoSeriesDissolution(page)

  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: /PNG/i }).click()
  expect((await download).suggestedFilename()).toBe('pk_chart.png')
})

test('sidebar collapse persists across reload', async ({ page }) => {
  await page.goto('/')

  const collapseButton = page.getByRole('button', { name: 'Collapse sidebar' })
  await expect(collapseButton).toBeVisible()
  await collapseButton.click()

  await expect(page.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()
  expect(await page.evaluate(() => window.localStorage.getItem('openpkflow.sidebar.collapsed'))).toBe('1')

  await page.reload()
  await expect(page.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()
})

test('mobile nav opens, closes, and auto-closes on navigation', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 })
  await page.goto('/')

  const aside = page.locator('aside').first()
  const openButton = page.getByRole('button', { name: 'Open sidebar' })
  await expect(openButton).toBeVisible()

  const asideClass = () => aside.evaluate((el) => el.className)

  expect(await asideClass()).toContain('-translate-x-full')

  await openButton.click()
  await expect.poll(asideClass).toContain('translate-x-0')
  await expect.poll(asideClass).not.toContain('-translate-x-full')

  await page.getByRole('button', { name: 'Close sidebar' }).click()
  await expect.poll(asideClass).toContain('-translate-x-full')

  await openButton.click()
  await expect.poll(asideClass).toContain('translate-x-0')

  await page.getByRole('link', { name: 'NCA', exact: true }).click()
  await expect(page).toHaveURL(/\/nca$/)
  await expect.poll(asideClass).toContain('-translate-x-full')
})
