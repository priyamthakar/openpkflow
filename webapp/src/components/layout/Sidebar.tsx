import { NavLink } from 'react-router-dom'
import { FlaskConical, LineChart, Waves, Home, X, Activity, Scale } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/', label: 'Home', icon: Home, exact: true },
  { to: '/nca', label: 'NCA', icon: LineChart },
  { to: '/dissolution', label: 'Dissolution', icon: Waves },
  { to: '/sim', label: 'Simulation', icon: FlaskConical },
  { to: '/ivivc', label: 'IVIVC', icon: Activity },
  { to: '/be', label: 'Bioequivalence', icon: Scale },
]

export function Sidebar({
  mobileOpen,
  onClose,
}: {
  mobileOpen?: boolean
  onClose?: () => void
}) {
  return (
    <aside
      className={cn(
        'bg-surface border-r border-border flex flex-col shrink-0 transition-all duration-300',
        'w-[220px] lg:w-[220px]',
        'max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-50 max-lg:w-60',
        mobileOpen ? 'max-lg:translate-x-0' : 'max-lg:-translate-x-full',
        'max-md:shadow-xl',
      )}
    >
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="font-mono-ui w-7 h-7 rounded-sm bg-accent flex items-center justify-center text-[#04122b] font-bold text-sm">
            PK
          </div>
          <span className="font-semibold text-[15.5px] text-text tracking-tight">
            OpenPKFlow
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="lg:hidden p-1 rounded-sm text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="flex-1 py-3 flex flex-col gap-0.5">
        <div className="font-mono-ui px-4 pb-2 text-[11px] uppercase tracking-[0.16em] text-text-dim">
          Analysis
        </div>
        {NAV.map(({ to, label, icon: Icon, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 px-4 py-2 border-l-[3px] text-[14.5px] font-medium transition-all duration-150',
                isActive
                  ? 'bg-surface-2 text-text border-l-accent'
                  : 'text-text-muted hover:text-text hover:bg-surface-2 border-l-transparent',
              )
            }
          >
            <Icon size={15} aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="font-mono-ui mt-auto px-4 py-3 text-xs text-text-dim border-t border-border">
        v2.4.0 / MIT
      </div>
    </aside>
  )
}
