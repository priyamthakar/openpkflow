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

test('MAP flow submits a chronological oral profile and renders usable metrics', async ({ page }) => {
  await page.route('**/api/bayes/map/analyze', async (route) => {
    const payload = route.request().postDataJSON()
    expect(payload.route).toBe('oral')
    expect(payload.times).toEqual([0.25, 1.12, 3.82, 9.05, 24.37])
    await route.fulfill({
      json: {
        subject: 'Theoph subject 1', route: 'oral', dose: 320, n_observations: 5,
        converged: true, uncertainty_reliable: true, fit_usable: true,
        CL_F: 3.5, Vz_F: 40, ka: 1.1, CL: null, Vz: null,
        CL_F_se: 0.2, Vz_F_se: 2, ka_se: 0.1, CL_se: null, Vz_se: null,
        k: 0.0875, half_life: 7.9, AUCinf: 91.4, Cmax: 6.8, Tmax: 1.9,
        gradient_norm: 0.0001, condition_number: 100, objective_value: 4,
        time_points: [0.25, 1.12, 3.82, 9.05, 24.37],
        observed_conc: [2.84, 10.5, 8.58, 6.89, 3.28],
        predicted_conc: [2.8, 10.4, 8.6, 6.8, 3.3], warnings: [],
        scope_note: 'screening only', disclaimer,
      },
    })
  })

  await page.goto('/bayes/map')
  await page.getByRole('button', { name: 'Run MAP Individual PK' }).click()
  await expect(page.getByText('CL/F').first()).toBeVisible()
  await expect(page.getByText('3.500').first()).toBeVisible()
})

test('MAP unusable fit suppresses estimates and report download', async ({ page }) => {
  await page.route('**/api/bayes/map/analyze', async (route) => {
    await route.fulfill({
      json: {
        subject: 'S01', route: 'oral', dose: 320, n_observations: 5,
        converged: false, uncertainty_reliable: false, fit_usable: false,
        CL_F: 3.5, Vz_F: 40, ka: 1.1, CL: null, Vz: null,
        CL_F_se: null, Vz_F_se: null, ka_se: null, CL_se: null, Vz_se: null,
        k: 0.0875, half_life: 7.9, AUCinf: 91.4, Cmax: 6.8, Tmax: 1.9,
        gradient_norm: null, condition_number: null, objective_value: null,
        time_points: [0.25, 1.12, 3.82, 9.05, 24.37],
        observed_conc: [2.84, 10.5, 8.58, 6.89, 3.28],
        predicted_conc: [2.8, 10.4, 8.6, 6.8, 3.3], warnings: ['fit failed'],
        scope_note: 'screening only', disclaimer,
      },
    })
  })

  await page.goto('/bayes/map')
  await page.getByRole('button', { name: 'Run MAP Individual PK' }).click()
  await expect(page.getByText('Fit unusable')).toBeVisible()
  await expect(page.getByText('CL/F')).not.toBeVisible()
  await expect(page.getByRole('button', { name: /Download/i })).not.toBeVisible()
})

test('alcohol screening sends the edited control time grid', async ({ page }) => {
  await page.route('**/api/supac/alcohol', async (route) => {
    const payload = route.request().postDataJSON()
    expect(payload.time_points).toEqual([5, 10, 15, 20, 30])
    expect(payload.ethanol_profiles[0].means).toHaveLength(5)
    await route.fulfill({
      json: {
        control_label: 'aqueous', f2_by_ethanol_pct: { '5': 95, '20': 40 },
        f2_threshold: 50, f2_method: 'regulatory', overall_pass: false,
        scope_note: 'screening only', disclaimer,
      },
    })
  })

  await page.goto('/supac')
  await page.getByRole('tab', { name: 'Alcohol dose dumping' }).click()
  await page.getByRole('button', { name: 'Assess alcohol dose dumping' }).click()
  await expect(page.getByText('Fail (regulatory f2)')).toBeVisible()
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

test('formal BE ANOVA flow renders ANOVA result', async ({ page }) => {
  await page.route('**/api/be/anova/analyze', async (route) => {
    await route.fulfill({
      json: {
        parameter: 'AUCinf', design: 'complete_balanced_2x2', n_subjects: 4,
        alpha: 0.05, confidence_level_pct: 90, be_lower: 0.8, be_upper: 1.25,
        treatment_log_lsmean: 4.7, reference_log_lsmean: 4.6,
        treatment_difference: 0.0959, treatment_se: 0.0096,
        residual_mse: 0.00018, residual_df: 2, cv_intra_pct: 1.4,
        gmr: 1.1007, gmr_lower_ci: 1.0703, gmr_upper_ci: 1.1319,
        decision: 'PASS',
        anova: [
          { source: 'Sequence', df: 1, sum_squares: 0.018, mean_square: 0.018, f_value: 2.4, p_value: 0.25 },
          { source: 'Residual', df: 2, sum_squares: 0.00036, mean_square: 0.00018, f_value: null, p_value: null },
        ],
        disclaimer,
      },
    })
  })

  await page.goto('/be/anova')
  await page.setInputFiles('input[type="file"]', {
    name: 'formal_be.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('subject,sequence,period,treatment,AUCinf\nS1,TR,1,T,110'),
  })
  await page.getByRole('button', { name: 'Run Formal ANOVA' }).click()
  await expect(page.getByText('Formal ANOVA result')).toBeVisible()
  await expect(page.getByText('Sequence').last()).toBeVisible()
  await expect(page.getByText('1.101').first()).toBeVisible()
})

test('RSABE flow renders PASS decision', async ({ page }) => {
  await page.route('**/api/be/rsabe/analyze', async (route) => {
    await route.fulfill({
      json: {
        parameter: 'AUC', decision: 'PASS', design: 'partial_replicate_2x2x3',
        jurisdiction: 'FDA', validation_status: 'VALIDATED',
        message: 'SABE demonstrated: aggregate criterion 95% upper bound < 0.',
        n_subjects: 51, alpha: 0.05, confidence_level_pct: 90,
        delta_hat: 0.0557, delta_ci_lower: -0.0393, delta_ci_upper: 0.1508,
        gmr: 1.0573, gmr_ci_lower: 0.9614, gmr_ci_upper: 1.1628,
        sigma_wr: 0.3421, sigma_wr_ci_lower: 0.2936, sigma_wr_ci_upper: 0.4119,
        cv_wr_pct: 35.23, highly_variable: true, theta: 0.7967,
        aggregate_criterion_point: -0.0901, aggregate_criterion_upper: -0.0438,
        point_estimate_constraint_met: true,
        disclaimer,
      },
    })
  })

  await page.goto('/be/rsabe')
  await page.setInputFiles('input[type="file"]', {
    name: 'rsabe.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('subject,sequence,period,treatment,AUC\nS1,TRR,1,T,110'),
  })
  await page.getByRole('button', { name: 'Run RSABE' }).click()
  await expect(page.getByText('RSABE result')).toBeVisible()
  await expect(page.getByText('PASS')).toBeVisible()
  await expect(page.getByText('Highly variable (CVwR >= 30%)', { exact: true })).toBeVisible()
  await expect(page.getByText('1.057').first()).toBeVisible()
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
          openpkflow_version: '2.7.0',
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

test('Sparse NCA example renders model fit and downloads screening report', async ({ page }) => {
  await page.route('**/api/nca/sparse/analyze', async (route) => {
    await route.fulfill({
      json: {
        subject: 'Theoph subject 1',
        dose: 320,
        route: 'oral',
        n_samples: 5,
        converged: true,
        CL_F: 1.58688,
        Vz_F: 28.6106,
        ka: 1.77941,
        k: 0.05546,
        half_life: 12.4972,
        CL_F_se: 0.4375,
        Vz_F_se: 4.2897,
        ka_se: 0.7595,
        AUClast: 149.9665,
        AUCinf: 201.654,
        Cmax: 10.0031,
        Tmax: 1.9779,
        time_points: [0.25, 1.12, 3.82, 9.05, 24.37],
        observed_conc: [2.84, 10.5, 8.58, 6.89, 3.28],
        fitted_conc: [3.9865, 9.2758, 9.3273, 6.9884, 2.9878],
        warnings: [],
        scope_note: 'Model-informed one-compartment oral screening estimate.',
        disclaimer,
      },
    })
  })
  await page.route('**/api/nca/sparse/report?format=html', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'text/html',
      headers: { 'content-disposition': 'attachment; filename="sparse_nca_report.html"' },
      body: '<!doctype html><html><head></head><body><h1>Sparse NCA</h1></body></html>',
    })
  })

  await page.goto('/nca/sparse')
  await page.getByRole('button', { name: 'Run Sparse NCA' }).click()

  await expect(page.getByText('Fit converged')).toBeVisible()
  await expect(page.getByText('1.587')).toBeVisible()
  await expect(page.getByText('Model-informed one-compartment oral screening estimate.')).toBeVisible()

  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download Report' }).click()
  await expect((await download).suggestedFilename()).toBe('sparse_nca_report.html')
})
