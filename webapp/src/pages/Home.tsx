import { useNavigate } from 'react-router-dom'
import { Activity, Info, LineChart, Mail, Scale, Waves, FlaskConical } from 'lucide-react'
import { useOutletContext } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'

const MODULES = [
  {
    to: '/nca',
    icon: LineChart,
    title: 'Non-Compartmental Analysis',
    desc: 'Upload PK concentration-time data. Compute AUC, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F and download a professional HTML/PDF report.',
    accent: 'var(--accent)',
    hint: 'Drag & drop CSV or paste from Excel',
  },
  {
    to: '/dissolution',
    icon: Waves,
    title: 'Dissolution Similarity',
    desc: 'Compare reference vs. test dissolution profiles using FDA f1/f2 metrics. View regulatory warnings and download reports.',
    accent: 'var(--success)',
    hint: 'Multi-batch formulation profiles',
  },
  {
    to: '/sim',
    icon: FlaskConical,
    title: 'PK Simulation',
    desc: 'Interactive 1-/2-compartment PK playground. Drag sliders to explore oral, IV bolus, and infusion profiles in real time.',
    accent: 'var(--warning)',
    hint: 'Live-updating concentration-time curves',
  },
  {
    to: '/ivivc',
    icon: Activity,
    title: 'IVIVC Level A',
    desc: 'Run Wagner-Nelson or Loo-Riegelman deconvolution, Levy correlation, predicted-vs-observed checks, and percent prediction error summaries.',
    accent: '#c084fc',
    hint: 'Paste in vivo, dissolution, and IV reference data',
  },
  {
    to: '/be',
    icon: Scale,
    title: 'Bioequivalence',
    desc: 'Analyze paired 2x2 crossover data using TOST, GMR, 90% confidence intervals, intra-subject CV, and clear pass/fail reporting.',
    accent: '#38bdf8',
    hint: 'Upload CSV or paste subject-level T/R values',
  },
]

export default function Home() {
  const navigate = useNavigate()
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="OpenPKFlow"
        subtitle="Open-source pharmacometric analysis"
        onMenuClick={onMenuClick}
      />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-5 py-10 lg:py-14">
          {/* Hero */}
          <div className="mb-10 animate-fade-in grid gap-8 md:grid-cols-[1fr_340px] xl:grid-cols-[1fr_380px] md:items-end">
            <div>
            <h2 className="text-4xl lg:text-6xl font-bold tracking-tight text-text mb-4 leading-none">
              Open-source pharmacometric analysis.
            </h2>
            <p className="text-base lg:text-lg text-text-muted max-w-2xl leading-relaxed font-medium">
              Upload your data, run validated NCA, dissolution, or PK simulation analyses in
              seconds, and download professional reports using the open-source openpkflow
              engine.
            </p>
            <div className="mt-5 flex items-start gap-2 rounded-sm border border-warning/30 bg-warning/5 px-4 py-2.5 text-warning text-sm leading-relaxed max-w-2xl">
              <Info size={15} className="mt-0.5 shrink-0" />
              <span>
                Not a regulatory tool. Results must be reviewed by qualified experts before any
                regulatory use.
              </span>
            </div>
            <div className="mt-5 border border-border bg-surface p-4 max-w-2xl">
              <p className="font-mono-ui text-[11px] uppercase tracking-[0.14em] text-text-dim">
                Built by
              </p>
              <h3 className="mt-1 text-xl font-semibold text-text">Priyam Thakar</h3>
              <p className="mt-1 text-sm leading-relaxed text-text-muted">
                Computational drug delivery specialist and PhD Scholar, Nirma University.
              </p>
              <a
                href="mailto:priyamthakar1@gmail.com"
                className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-accent no-underline hover:text-accent-hover"
              >
                <Mail size={15} aria-hidden="true" />
                priyamthakar1@gmail.com
              </a>
            </div>
            </div>

            <div className="block border border-border bg-surface p-3 shadow-2xl shadow-black/20">
              <div className="h-7 border-b border-border bg-surface-2 -m-3 mb-3 flex items-center gap-1.5 px-3">
                <span className="h-2 w-2 rounded-full bg-border-2" />
                <span className="h-2 w-2 rounded-full bg-border-2" />
                <span className="h-2 w-2 rounded-full bg-border-2" />
                <span className="font-mono-ui ml-2 text-[11px] uppercase tracking-[0.12em] text-text-dim">
                  NCA / Subject S01
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[
                  ['Cmax', '6.800'],
                  ['AUClast', '65.200'],
                  ['t1/2', '4.903'],
                ].map(([label, value]) => (
                  <div key={label} className="border border-border bg-bg p-3">
                    <p className="font-mono-ui text-[10px] uppercase tracking-[0.12em] text-text-dim">
                      {label}
                    </p>
                    <p className="font-mono-ui mt-2 text-xl font-bold text-accent">{value}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 h-36 border border-border bg-bg p-3">
                <svg viewBox="0 0 320 120" className="h-full w-full overflow-visible">
                  <polyline
                    fill="none"
                    stroke="var(--accent)"
                    strokeWidth="3"
                    points="0,105 40,80 78,38 118,28 172,54 230,76 320,96"
                  />
                  <line x1="0" y1="105" x2="320" y2="105" stroke="var(--border)" />
                  <line x1="0" y1="10" x2="0" y2="105" stroke="var(--border)" />
                </svg>
              </div>
            </div>
          </div>

          {/* Feature cards */}
          <h3 className="font-mono-ui mb-4 text-[12px] uppercase tracking-[0.16em] text-text-muted">
            Analysis modules
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {MODULES.map(({ to, icon: Icon, title, desc, accent, hint }) => (
              <button
                key={to}
                onClick={() => navigate(to)}
                className="group text-left bg-surface border border-border rounded-sm p-5
                  hover:border-accent/30 hover:-translate-y-1 hover:shadow-lg
                  transition-all duration-200
                  focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
              >
                <div
                  className="w-10 h-10 rounded-sm flex items-center justify-center mb-3.5 transition-transform group-hover:scale-110"
                  style={{
                    background: `color-mix(in srgb, ${accent} 14%, transparent)`,
                    color: accent,
                  }}
                >
                  <Icon size={20} />
                </div>
                <h3 className="text-base font-semibold text-text mb-1.5">{title}</h3>
                <p className="text-sm text-text-muted leading-relaxed mb-3">{desc}</p>
                <span className="font-mono-ui text-[11px] uppercase tracking-[0.08em] text-text-dim group-hover:text-text-muted transition-colors">
                  {hint}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
