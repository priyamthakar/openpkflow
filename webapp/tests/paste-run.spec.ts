import { expect, test } from '@playwright/test'

const disclaimer =
  'This report was generated using OpenPKFlow (open-source). Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.'

test('NCA paste-run flow renders metrics', async ({ page }) => {
  await page.route('**/api/nca/analyze', async (route) => {
    await route.fulfill({
      json: {
        columns: ['subject', 'AUClast', 'AUCinf_obs', 'Cmax', 'Tmax', 'half_life', 'CL_F'],
        subjects: [
          { subject: 'S01', AUClast: 65.2, AUCinf_obs: 68.4, Cmax: 6.8, Tmax: 4, half_life: 4.9, CL_F: 4.68 },
        ],
        profiles: [
          {
            subject: 'S01',
            times: [0, 1, 2, 4, 8, 12, 24],
            concs: [0, 2.4, 5.6, 6.8, 4.1, 2.2, 0.4],
            lambda_z_times: [8, 12, 24],
            lambda_z_concs: [4.1, 2.2, 0.4],
          },
        ],
        warnings: [],
        disclaimer,
      },
    })
  })

  await page.goto('/nca')
  await page.getByRole('radio', { name: 'Paste table' }).click()
  await page.getByRole('button', { name: 'Run NCA' }).click()
  await expect(page.getByText('Cmax').first()).toBeVisible()
  await expect(page.getByText('6.800').first()).toBeVisible()
})

test('Dissolution paste-run flow renders f2 result', async ({ page }) => {
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
  await expect(page.getByText('86.400')).toBeVisible()
})

test('Simulation paste-style parameter flow renders live curve metrics', async ({ page }) => {
  await page.route('**/api/sim/simulate', async (route) => {
    await route.fulfill({
      json: {
        times: [0, 1, 2, 4, 8, 12],
        concs: [0, 2, 5, 4, 2, 1],
        dose_times: [0],
        Cmax: 5,
        Tmax: 2,
        Cmin: 0,
        Clast: 1,
        warnings: [],
        disclaimer,
      },
    })
  })

  await page.goto('/sim')
  await expect(page.getByText('Cmax')).toBeVisible()
  await expect(page.getByText('5.000')).toBeVisible()
})

test('IVIVC paste-run flow renders acceptance summary', async ({ page }) => {
  await page.route('**/api/ivivc/analyze', async (route) => {
    await route.fulfill({
      json: {
        method: 'wagner_nelson',
        study_label: '',
        times: [0, 1, 2, 4],
        concentrations: [0, 0.5, 1.2, 2.1],
        fa: [0, 0.2, 0.45, 0.8],
        levy_slope: 1,
        levy_intercept: 0,
        levy_r_squared: 0.96,
        ivt_times: [0, 1, 2, 4],
        ivt_fraction: [0, 0.25, 0.5, 0.85],
        predicted_times: [0, 1, 2, 4],
        predicted_concs: [0, 0.48, 1.1, 2.0],
        pe_cmax: 4.2,
        pe_auc: 5.1,
        mean_abs_pe: 4.8,
        overall_pass: true,
        disclaimer,
      },
    })
  })

  await page.goto('/ivivc')
  await page.getByRole('button', { name: 'Run IVIVC' }).click()
  await expect(page.getByText('IVIVC Acceptable')).toBeVisible()
  await expect(page.getByText('0.960')).toBeVisible()
})

test('BE paste-run flow renders bioequivalence verdict', async ({ page }) => {
  await page.route('**/api/be/analyze', async (route) => {
    await route.fulfill({
      json: {
        parameter: 'AUCinf',
        n: 6,
        gmr: 0.96,
        gmr_lower_90ci: 0.91,
        gmr_upper_90ci: 1.04,
        be_lower: 0.8,
        be_upper: 1.25,
        bioequivalent: true,
        cv_intra_pct: 12.2,
        subjects: [
          { subject: 'S01', sequence: 'RT', reference: 100.2, test: 96.4, ratio: 0.962, log_diff: -0.039 },
        ],
        disclaimer,
      },
    })
  })

  await page.goto('/be')
  await page.getByRole('radio', { name: 'Paste table' }).click()
  await page.getByRole('button', { name: 'Run BE Analysis' }).click()
  await expect(page.getByText('BIOEQUIVALENT')).toBeVisible()
  await expect(page.getByText('0.960')).toBeVisible()
})
