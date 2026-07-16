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

test('BE power calculator happy path', async ({ page }) => {
  await page.route('**/api/be/power', async (route) => {
    await route.fulfill({
      json: {
        power: 0.834,
        gmr: 0.95,
        cv: 0.2,
        n: 24,
        be_lower: 0.8,
        be_upper: 1.25,
        alpha: 0.05,
        disclaimer,
      },
    })
  })

  await page.goto('/be')
  await page.getByRole('radio', { name: 'Power calculator' }).click()
  await page.getByRole('button', { name: 'Compute Power' }).click()
  await expect(page.getByText('Power').first()).toBeVisible()
  await expect(page.getByText('0.834')).toBeVisible()
})

test('Multi-media dissolution tab renders overall pass', async ({ page }) => {
  await page.route('**/api/dissolution/multi-media/analyze', async (route) => {
    await route.fulfill({
      json: {
        reference_label: 'reference',
        test_label: 'test',
        media_names: ['pH 1.2', 'pH 4.5', 'pH 6.8'],
        f2_summary: { 'pH 1.2': 72.1, 'pH 4.5': 68.4, 'pH 6.8': 70.2 },
        overall_pass: true,
        per_media: [
          {
            medium: 'pH 1.2',
            f1_value: 3.2,
            f2_value: 72.1,
            similar: true,
            n_timepoints: 7,
            time_points: [5, 10, 15, 20, 30, 45, 60],
            reference_mean: [5, 15, 30, 45, 60, 80, 95],
            test_mean: [6, 16, 31, 44, 58, 78, 93],
          },
          {
            medium: 'pH 4.5',
            f1_value: 3.5,
            f2_value: 68.4,
            similar: true,
            n_timepoints: 7,
            time_points: [5, 10, 15, 20, 30, 45, 60],
            reference_mean: [5, 15, 30, 45, 60, 80, 95],
            test_mean: [6, 16, 31, 44, 58, 78, 93],
          },
          {
            medium: 'pH 6.8',
            f1_value: 3.1,
            f2_value: 70.2,
            similar: true,
            n_timepoints: 7,
            time_points: [5, 10, 15, 20, 30, 45, 60],
            reference_mean: [5, 15, 30, 45, 60, 80, 95],
            test_mean: [6, 16, 31, 44, 58, 78, 93],
          },
        ],
        disclaimer,
      },
    })
  })

  await page.goto('/dissolution')
  await page.getByRole('radio', { name: 'Multi-media' }).click()
  await page.getByRole('button', { name: 'Run Multi-Media f2' }).click()
  await expect(page.getByText('Overall PASS (all f2 >= 50)')).toBeVisible()
  await expect(page.getByText('72.100')).toBeVisible()
})

test('IVIVC load example restores paste grids', async ({ page }) => {
  await page.goto('/ivivc')
  await page.getByRole('button', { name: 'Load example' }).click()
  await expect(page.locator('input[value="Example IR tablet"]')).toBeVisible()
})

test('Study pipeline runs uploaded stages and downloads report and audit bundle', async ({ page }) => {
  await page.route('**/api/pipeline/analyze', async (route) => {
    await route.fulfill({
      json: {
        metadata: {
          title: 'Pipeline browser test',
          openpkflow_version: '2.6.0',
          generated_at_utc: '2026-07-16T08:00:00Z',
          stages_requested: ['dissolution'],
          stages_completed: ['dissolution'],
          stage_status: { dissolution: 'completed' },
          warnings: [],
          config: { dissolution_csv: 'dissolution.csv' },
        },
        dissolution: {
          reference_label: 'reference',
          test_label: 'test',
          f1_value: 1.8,
          f2_value: 82.4,
          n_timepoints: 6,
          time_points: [5, 10, 15, 20, 30, 45],
          reference_mean: [15, 32, 50, 68, 85, 95],
          test_mean: [14, 31, 49, 66, 83, 94],
          f2_method: 'regulatory',
          warnings: [],
        },
        nca: null,
        be: null,
        disclaimer,
      },
    })
  })
  await page.route('**/api/pipeline/report', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'text/html',
      headers: { 'content-disposition': 'attachment; filename="study_pipeline_report.html"' },
      body: '<!doctype html><html><head></head><body><h1>Pipeline browser test</h1></body></html>',
    })
  })
  await page.route('**/api/pipeline/audit-bundle', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/zip',
      headers: { 'content-disposition': 'attachment; filename="openpkflow_audit_bundle.zip"' },
      body: 'mock zip content',
    })
  })

  await page.goto('/pipeline')
  await page.locator('input[type="file"]').first().setInputFiles({
    name: 'dissolution.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('formulation,batch,time,percent_released\nreference,R1,5,15\ntest,T1,5,14'),
  })
  await page.getByLabel('Report title').fill('Pipeline browser test')
  await page.getByRole('button', { name: 'Run Study Pipeline' }).click()

  await expect(page.getByText('Pipeline complete')).toBeVisible()
  await expect(page.getByText('82.400')).toBeVisible()

  const reportDownload = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download Report' }).click()
  await expect((await reportDownload).suggestedFilename()).toBe('study_pipeline_report.html')

  const auditDownload = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download Audit ZIP' }).click()
  await expect((await auditDownload).suggestedFilename()).toBe('openpkflow_audit_bundle.zip')
})
