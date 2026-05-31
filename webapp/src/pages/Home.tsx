import { useNavigate } from 'react-router-dom'
import { LineChart, Waves, FlaskConical } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'

const MODULES = [
  {
    to: '/nca',
    icon: LineChart,
    title: 'Non-Compartmental Analysis',
    desc: 'Upload PK concentration-time data. Compute AUC, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F and download a professional HTML/PDF report.',
    accent: '#5e6ad2',
  },
  {
    to: '/dissolution',
    icon: Waves,
    title: 'Dissolution Similarity',
    desc: 'Compare reference vs. test dissolution profiles using FDA f1/f2 metrics. View regulatory warnings and download reports.',
    accent: '#3dd68c',
  },
  {
    to: '/sim',
    icon: FlaskConical,
    title: 'PK Simulation',
    desc: 'Interactive 1-/2-compartment PK playground. Drag sliders to explore oral, IV bolus, and infusion profiles in real time.',
    accent: '#f0a731',
  },
]

export function Home() {
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar title="OpenPKFlow" subtitle="Open-source pharmacometric analysis" />

      <div style={{ flex: 1, overflowY: 'auto', padding: 36 }}>
        {/* Hero */}
        <div style={{ maxWidth: 640, marginBottom: 48 }}>
          <h2 style={{ fontSize: 28, fontWeight: 700, lineHeight: 1.3, marginBottom: 12, color: 'var(--text)' }}>
            Transparent, reproducible pharmacometrics
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.7 }}>
            Upload your data, run validated NCA, dissolution, or PK simulation analyses
            in seconds, and download professional reports — powered by the open-source
            openpkflow engine.
          </p>
          <div
            style={{
              marginTop: 16,
              padding: '10px 14px',
              background: 'rgba(240,167,49,0.06)',
              border: '1px solid rgba(240,167,49,0.2)',
              borderRadius: 'var(--radius)',
              fontSize: 12,
              color: 'var(--text-muted)',
            }}
          >
            Not a regulatory tool. Results must be reviewed by qualified experts before any
            regulatory use.
          </div>
        </div>

        {/* Module cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {MODULES.map(({ to, icon: Icon, title, desc, accent }) => (
            <button
              key={to}
              onClick={() => navigate(to)}
              style={{
                textAlign: 'left',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 10,
                padding: 24,
                cursor: 'pointer',
                transition: 'border-color 0.15s, transform 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = accent
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.transform = 'none'
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  background: `${accent}22`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 14,
                }}
              >
                <Icon size={18} color={accent} />
              </div>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>{title}</h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>{desc}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
