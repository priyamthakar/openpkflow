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
