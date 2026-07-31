import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { Sigma } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { EmptyResults } from '@/components/shared/EmptyResults'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { MetricCard } from '@/components/shared/MetricCard'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { analyzeRsabe, downloadRsabeReport } from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type { RsabeResponse } from '@/lib/types'

const OPTIONS = {
  parameter: 'AUC',
  subject_col: 'subject',
  sequence_col: 'sequence',
  period_col: 'period',
  treatment_col: 'treatment',
}

const BADGE_VARIANT: Record<RsabeResponse['decision'], 'success' | 'danger' | 'warning'> = {
  PASS: 'success',
  FAIL: 'danger',
  NOT_EVALUABLE: 'warning',
}

export default function RsabePage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [file, setFile] = useState<File | null>(null)
  const mutation = useMutation<RsabeResponse, Error>({
    mutationFn: () => analyzeRsabe(file as File, OPTIONS),
  })
  const result = mutation.data

  useRunShortcut(mutation.mutate, Boolean(file) && !mutation.isPending)

  return (
    <div className="flex h-full flex-col">
      <TopBar title="FDA Partial-Replicate RSABE" subtitle="TRR / RTR / RRT design only" onMenuClick={onMenuClick} />
      <AnalysisShell resultKey={Boolean(result)}>
        <div className="flex flex-col gap-5">
          <section className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
            <p className="font-semibold">Validated scope</p>
            <p className="mt-1">Requires long-format TRR/RTR/RRT partial-replicate data with subject, sequence, period, treatment, and endpoint columns, with equal subjects per sequence (unbalanced allocation, e.g. from unequal dropout, is rejected rather than silently biased). Applies only when the reference is highly variable (CVwR &gt;= 30%); otherwise the result is NOT_EVALUABLE and standard average BE should be used.</p>
          </section>
          <FileDropzone onFile={(next) => { setFile(next); mutation.reset() }} onClear={() => { setFile(null); mutation.reset() }} label="Upload partial-replicate CSV" />
          <Button size="lg" className="w-full" disabled={!file || mutation.isPending} loading={mutation.isPending} onClick={() => mutation.mutate()}>
            {mutation.isPending ? 'Evaluating RSABE...' : 'Run RSABE'}
          </Button>
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {mutation.isError && <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />}
          {!result && !mutation.isPending && !mutation.isError && (
            <EmptyResults
              icon={Sigma}
              title="No RSABE result yet"
              description="Upload long-format TRR/RTR/RRT partial-replicate data to evaluate reference-scaled average bioequivalence."
            />
          )}
          {result && <>
            <div className="flex items-center justify-between gap-3"><h2 className="text-lg font-bold text-text">RSABE result</h2><Badge variant={BADGE_VARIANT[result.decision]}>{result.decision}</Badge></div>
            <p className="text-sm text-text-muted">{result.message}</p>
            <div className="flex flex-wrap gap-3">
              <MetricCard label="GMR" value={result.gmr} highlight />
              <MetricCard label={`${result.confidence_level_pct}% CI lower`} value={result.gmr_ci_lower} />
              <MetricCard label={`${result.confidence_level_pct}% CI upper`} value={result.gmr_ci_upper} />
              <MetricCard label="CVwR" value={result.cv_wr_pct} unit="%" />
              <MetricCard label="Aggregate crit. (point)" value={result.aggregate_criterion_point} />
              <MetricCard label="Aggregate crit. (95% upper)" value={result.aggregate_criterion_upper} />
            </div>
            <div className="flex flex-wrap gap-2 text-sm">
              <Badge variant={result.highly_variable ? 'accent' : 'default'}>
                {result.highly_variable ? 'Highly variable (CVwR >= 30%)' : 'Not highly variable'}
              </Badge>
              <Badge variant={result.point_estimate_constraint_met ? 'success' : 'danger'}>
                Point estimate {result.point_estimate_constraint_met ? 'met' : 'not met'}
              </Badge>
            </div>
            <DownloadReportButton formats={['html', 'markdown']} onDownload={(format) => downloadRsabeReport(file as File, OPTIONS, format)} />
            <Disclaimer text={result.disclaimer} />
          </>}
        </div>
      </AnalysisShell>
    </div>
  )
}
