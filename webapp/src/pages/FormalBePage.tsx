import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { Scale } from 'lucide-react'
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
import { analyzeFormalBe, downloadFormalBeReport } from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type { FormalBeResponse } from '@/lib/types'

const OPTIONS = {
  parameter: 'AUCinf',
  subject_col: 'subject',
  sequence_col: 'sequence',
  period_col: 'period',
  treatment_col: 'treatment',
}

export default function FormalBePage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [file, setFile] = useState<File | null>(null)
  const mutation = useMutation<FormalBeResponse, Error>({
    mutationFn: () => analyzeFormalBe(file as File, OPTIONS),
  })
  const result = mutation.data

  useRunShortcut(mutation.mutate, Boolean(file) && !mutation.isPending)

  return (
    <div className="flex h-full flex-col">
      <TopBar title="Formal 2x2 BE ANOVA" subtitle="Complete balanced TR/RT crossover only" onMenuClick={onMenuClick} />
      <AnalysisShell resultKey={Boolean(result)}>
        <div className="flex flex-col gap-5">
          <section className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
            <p className="font-semibold">Validated scope</p>
            <p className="mt-1">Requires complete, balanced long-format TR/RT data with subject, sequence, period, treatment, and AUCinf columns. Incomplete or unbalanced studies fail closed.</p>
          </section>
          <FileDropzone onFile={(next) => { setFile(next); mutation.reset() }} onClear={() => { setFile(null); mutation.reset() }} label="Upload formal 2x2 CSV" />
          <Button size="lg" className="w-full" disabled={!file || mutation.isPending} loading={mutation.isPending} onClick={() => mutation.mutate()}>
            {mutation.isPending ? 'Fitting ANOVA...' : 'Run Formal ANOVA'}
          </Button>
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {mutation.isError && <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />}
          {!result && !mutation.isPending && !mutation.isError && (
            <EmptyResults
              icon={Scale}
              title="No formal ANOVA yet"              description="Upload complete balanced long-format TR/RT crossover data to run the formal model."
            />
          )}
          {result && <>
            <div className="flex items-center justify-between gap-3"><h2 className="text-lg font-bold text-text">Formal ANOVA result</h2><Badge variant={result.decision === 'PASS' ? 'success' : 'danger'}>{result.decision}</Badge></div>
            <div className="flex flex-wrap gap-3"><MetricCard label="GMR" value={result.gmr} highlight /><MetricCard label={`${result.confidence_level_pct}% CI lower`} value={result.gmr_lower_ci} /><MetricCard label={`${result.confidence_level_pct}% CI upper`} value={result.gmr_upper_ci} /><MetricCard label="Residual CV" value={result.cv_intra_pct} unit="%" /><MetricCard label="Residual MSE" value={result.residual_mse} /></div>
            <AnovaTable result={result} />
            <DownloadReportButton formats={['html', 'markdown']} onDownload={(format) => downloadFormalBeReport(file as File, OPTIONS, format)} />
            <Disclaimer text={result.disclaimer} />
          </>}
        </div>
      </AnalysisShell>
    </div>
  )
}

function AnovaTable({ result }: { result: FormalBeResponse }) {
  return <div className="overflow-x-auto rounded-sm border border-border"><table className="w-full border-collapse text-sm"><thead><tr>{['Source', 'DF', 'SS', 'MS', 'F', 'p-value'].map((label) => <th key={label} className="bg-surface-2 px-3 py-2 text-left text-xs text-text-muted">{label}</th>)}</tr></thead><tbody>{result.anova.map((row) => <tr key={row.source}><td className="border-t border-border px-3 py-2">{row.source}</td><td className="border-t border-border px-3 py-2">{row.df}</td><td className="border-t border-border px-3 py-2">{row.sum_squares.toFixed(6)}</td><td className="border-t border-border px-3 py-2">{row.mean_square?.toFixed(6) ?? 'N/A'}</td><td className="border-t border-border px-3 py-2">{row.f_value?.toFixed(4) ?? 'N/A'}</td><td className="border-t border-border px-3 py-2">{row.p_value?.toFixed(6) ?? 'N/A'}</td></tr>)}</tbody></table></div>
}
