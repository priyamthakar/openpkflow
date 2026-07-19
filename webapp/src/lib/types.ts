/** TypeScript mirrors of the FastAPI response schemas. */

export interface SubjectProfile {
  subject: string
  times: number[]
  concs: number[]
  lambda_z_times: number[]
  lambda_z_concs: number[]
}

export interface NcaResponse {
  columns: string[]
  subjects: Record<string, number | string | null>[]
  profiles: SubjectProfile[]
  warnings: string[]
  disclaimer: string
}

export interface FormulationsResponse {
  formulations: string[]
}

export interface CompareResponse {
  reference_label: string
  test_label: string
  f1_value: number
  f2_value: number
  similar: boolean
  n_timepoints: number
  time_points: number[]
  reference_mean: number[]
  test_mean: number[]
  warnings: string[]
  disclaimer: string
}

export interface SimResponse {
  times: number[]
  concs: number[]
  dose_times: number[]
  Cmax: number
  Tmax: number
  Cmin: number
  Clast: number
  warnings: string[]
  disclaimer: string
}

export interface HealthResponse {
  status: string
  engine_version: string
}

export interface IvIvcResponse {
  method: string
  study_label: string
  times: number[]
  concentrations: number[]
  fa: number[]
  levy_slope: number | null
  levy_intercept: number | null
  levy_r_squared: number | null
  ivt_times: number[]
  ivt_fraction: number[]
  predicted_times: number[]
  predicted_concs: number[]
  pe_cmax: number | null
  pe_auc: number | null
  mean_abs_pe: number | null
  overall_pass: boolean | null
  predictability_note?: string | null
  disclaimer: string
}

export interface BeSubjectRow {
  subject: string
  reference: number
  test: number
  ratio: number
  log_diff: number
  sequence?: string
}

export interface BeResponse {
  parameter: string
  n: number
  gmr: number
  gmr_lower_90ci: number
  gmr_upper_90ci: number
  be_lower: number
  be_upper: number
  bioequivalent: boolean
  cv_intra_pct: number
  subjects: BeSubjectRow[]
  disclaimer: string
}

export interface FormalBeAnovaRow {
  source: string
  df: number
  sum_squares: number
  mean_square: number | null
  f_value: number | null
  p_value: number | null
}

export interface FormalBeResponse {
  parameter: string
  design: string
  n_subjects: number
  alpha: number
  confidence_level_pct: number
  be_lower: number
  be_upper: number
  treatment_log_lsmean: number
  reference_log_lsmean: number
  treatment_difference: number
  treatment_se: number
  residual_mse: number
  residual_df: number
  cv_intra_pct: number
  gmr: number
  gmr_lower_ci: number
  gmr_upper_ci: number
  decision: 'PASS' | 'FAIL' | 'NOT_EVALUABLE'
  anova: FormalBeAnovaRow[]
  disclaimer: string
}

export interface BePowerRequest {
  gmr: number
  cv: number
  n: number
  be_lower?: number
  be_upper?: number
  alpha?: number
}

export interface BePowerResponse {
  power: number
  gmr: number
  cv: number
  n: number
  be_lower: number
  be_upper: number
  alpha: number
  disclaimer: string
}

export interface BeSampleSizeRequest {
  gmr: number
  cv: number
  target_power?: number
  be_lower?: number
  be_upper?: number
  alpha?: number
  max_n?: number
}

export interface BeSampleSizeResponse {
  n: number
  achieved_power: number
  gmr: number
  cv: number
  target_power: number
  be_lower: number
  be_upper: number
  alpha: number
  disclaimer: string
}

export interface DissolutionRowPayload {
  formulation: string
  batch: string
  time: number
  percent_released: number
}

export interface MultiMediaRequest {
  media: { name: string; rows: DissolutionRowPayload[] }[]
  reference_label: string
  test_label: string
}

export interface MediumCompareResult {
  medium: string
  f1_value: number
  f2_value: number
  similar: boolean
  n_timepoints: number
  time_points: number[]
  reference_mean: number[]
  test_mean: number[]
}

export interface MultiMediaResponse {
  reference_label: string
  test_label: string
  media_names: string[]
  f2_summary: Record<string, number>
  overall_pass: boolean
  per_media: MediumCompareResult[]
  disclaimer: string
}

export interface PipelineOptions {
  title: string
  dissolution_reference: string | null
  dissolution_test: string | null
  nca_auc_method: 'linear' | 'log' | 'linear_up_log_down' | null
  nca_blq_method: 'none' | 'drop' | 'zero' | 'half_lloq' | 'lloq' | 'm1' | 'm2' | null
  be_parameter: string
  be_reference_col: string
  be_test_col: string
  be_subject_col: string
  be_sequence_col: string | null
  be_lower: number
  be_upper: number
}

export interface PipelineFiles {
  dissolution?: File | null
  nca?: File | null
  be?: File | null
}

export interface PipelineMetadata {
  title: string
  openpkflow_version: string
  generated_at_utc: string
  stages_requested: string[]
  stages_completed: string[]
  stage_status: Record<string, string>
  warnings: string[]
  config: Record<string, unknown>
  methods?: Record<string, unknown>
}

export interface PipelineDissolutionResult {
  reference_label: string
  test_label: string
  f1_value: number
  f2_value: number
  n_timepoints: number
  time_points: number[]
  reference_mean: number[]
  test_mean: number[]
  f2_method: string
  warnings: string[]
}

export interface PipelineNcaResult {
  study_label: string
  auc_method: string
  blq_method: string
  n_subjects: number
  subjects: Record<string, number | string | null>[]
}

export interface PipelineBeResult {
  parameter: string
  n: number
  gmr: number
  gmr_lower_90ci: number
  gmr_upper_90ci: number
  be_lower: number
  be_upper: number
  bioequivalent: boolean
  cv_intra_pct: number
}

export interface PipelineResponse {
  metadata: PipelineMetadata
  dissolution: PipelineDissolutionResult | null
  nca: PipelineNcaResult | null
  be: PipelineBeResult | null
  disclaimer: string
}

export interface SparseNcaRequest {
  subject: string
  times: number[]
  concentrations: number[]
  dose: number
}

export interface SparseNcaResponse {
  subject: string
  dose: number
  route: 'oral'
  n_samples: number
  converged: boolean
  CL_F: number
  Vz_F: number
  ka: number
  k: number
  half_life: number
  CL_F_se: number | null
  Vz_F_se: number | null
  ka_se: number | null
  AUClast: number
  AUCinf: number
  Cmax: number
  Tmax: number
  time_points: number[]
  observed_conc: number[]
  fitted_conc: number[]
  warnings: string[]
  scope_note: string
  disclaimer: string
}

export interface MapPkRequest {
  subject: string
  times: number[]
  concentrations: number[]
  dose: number
  route: 'oral' | 'iv_bolus'
}

export interface MapPkResponse {
  subject: string
  route: 'oral' | 'iv_bolus'
  dose: number
  n_observations: number
  converged: boolean
  uncertainty_reliable: boolean
  fit_usable: boolean
  CL_F: number | null
  Vz_F: number | null
  ka: number | null
  CL: number | null
  Vz: number | null
  CL_F_se: number | null
  Vz_F_se: number | null
  ka_se: number | null
  CL_se: number | null
  Vz_se: number | null
  k: number
  half_life: number
  AUCinf: number
  Cmax: number
  Tmax: number
  gradient_norm: number | null
  condition_number: number | null
  objective_value: number | null
  time_points: number[]
  observed_conc: number[]
  predicted_conc: number[]
  warnings: string[]
  scope_note: string
  disclaimer: string
}

export type SupacComponentCategory =
  | 'filler'
  | 'binder'
  | 'disintegrant_starch'
  | 'disintegrant_other'
  | 'lubricant_stearate'
  | 'lubricant_other'
  | 'glidant'
  | 'film_coat'
  | 'non_critical'
  | 'critical'

export interface SupacClassifyRequest {
  component_category: SupacComponentCategory
  change_pct: number
}

export interface SupacClassifyResponse {
  level: 1 | 2 | 3
  change_pct: number
  component_category: string
  rationale: string
  recommended_tests: string[]
  scope_note: string
  disclaimer: string
}

export interface EthanolProfile {
  ethanol_pct: number
  means: number[]
}

export interface AlcoholDosingRequest {
  time_points: number[]
  control_means: number[]
  ethanol_profiles: EthanolProfile[]
  f2_threshold: number
  control_label: string
}

export interface AlcoholDosingResponse {
  control_label: string
  f2_by_ethanol_pct: Record<string, number>
  f2_threshold: number
  f2_method: 'regulatory'
  overall_pass: boolean
  scope_note: string
  disclaimer: string
}
