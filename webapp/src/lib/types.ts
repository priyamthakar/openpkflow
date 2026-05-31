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
