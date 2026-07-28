import { expect, test, type Page } from '@playwright/test'

const disclaimer =
  'This report was generated using OpenPKFlow (open-source). Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.'

async function mockHealth(page: Page) {
  await page.route('**/health', async (route) => {
    await route.fulfill({
      json: {
        status: 'ok',
        engine_version: '2.7.1',
        git_sha: 'abc123',
        git_branch: 'main',
        service_id: 'srv-test',
      },
    })
  })
}

async function openDissolutionResult(page: Page) {
  await mockHealth(page)
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

  await page.goto('/dissolution')
  await page.getByRole('radio', { name: 'Paste table' }).click()
  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page.getByText('Similar: f2 >= 50')).toBeVisible()
}

test('PK chart legend hides and restores a series', async ({ page }) => {
  await openDissolutionResult(page)
  const lines = page.locator('.recharts-line-curve')
  await expect(lines).toHaveCount(2)

  await page.getByText('Test', { exact: true }).last().click()
  await expect(lines).toHaveCount(1)

  await page.getByText('Test', { exact: true }).last().click()
  await expect(lines).toHaveCount(2)
})

test('PK chart exports a PNG download', async ({ page }) => {
  await openDissolutionResult(page)

  const downloadPromise = page.waitForEvent('download')
  await page.getByTitle('Download chart as PNG').click()
  const download = await downloadPromise

  expect(download.suggestedFilename()).toBe('pk_chart.png')
})

test('desktop sidebar collapse persists after reload', async ({ page }) => {
  await mockHealth(page)
  await page.goto('/')

  await page.getByRole('button', { name: 'Collapse sidebar' }).click()
  await expect(page.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()
  await expect
    .poll(() => page.evaluate(() => localStorage.getItem('openpkflow.sidebar.collapsed')))
    .toBe('1')

  await page.reload()
  await expect(page.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()
})

test('mobile menu opens, navigates, and closes', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await mockHealth(page)
  await page.goto('/')

  await page.getByRole('button', { name: 'Open sidebar' }).click()
  await expect(page.getByRole('button', { name: 'Close sidebar' })).toBeVisible()
  await page.getByRole('link', { name: 'Dissolution' }).click()

  await expect(page).toHaveURL(/\/dissolution$/)
  await expect
    .poll(async () => {
      const box = await page
        .getByRole('button', { name: 'Close sidebar' })
        .locator('xpath=ancestor::aside')
        .boundingBox()
      return box ? box.x + box.width : 0
    })
    .toBeLessThanOrEqual(0)
})
