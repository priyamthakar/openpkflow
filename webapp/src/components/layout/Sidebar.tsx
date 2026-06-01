import { NavLink } from 'react-router-dom'
import { FlaskConical, LineChart, Waves, Home } from 'lucide-react'

const NAV = [
  { to: '/', label: 'Home', icon: Home, exact: true },
  { to: '/nca', label: 'NCA', icon: LineChart },
  { to: '/dissolution', label: 'Dissolution', icon: Waves },
  { to: '/sim', label: 'Simulation', icon: FlaskConical },
]

export function Sidebar() {
  return (
    <aside
      style={{
        width: 220,
        minWidth: 220,
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        gap: 4,
      }}
    >
      {/* Logo */}
      <div style={{ padding: '0 20px 24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: 28,
              height: 28,
              background: 'var(--accent)',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 13,
              fontWeight: 700,
              color: '#fff',
            }}
          >
            PK
          </div>
          <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text)' }}>OpenPKFlow</span>
        </div>
      </div>

      <nav style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV.map(({ to, label, icon: Icon, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 12px',
              borderRadius: 6,
              color: isActive ? 'var(--text)' : 'var(--text-muted)',
              background: isActive ? 'var(--accent-muted)' : 'transparent',
              textDecoration: 'none',
              fontSize: 13,
              fontWeight: isActive ? 500 : 400,
              transition: 'all 0.15s',
            })}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div style={{ marginTop: 'auto', padding: '16px 20px', fontSize: 11, color: 'var(--text-dim)' }}>
        v2.4.0 · MIT License
      </div>
    </aside>
  )
}
