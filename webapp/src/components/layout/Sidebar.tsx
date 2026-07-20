import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  FlaskConical, LineChart, Waves, Home, X, Activity, Scale, Mail, Workflow,
  ScatterChart, Brain, ShieldCheck, PanelLeftClose, PanelLeftOpen, Sigma,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  to: string
  label: string
  icon: typeof Home
  exact?: boolean
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Overview',
    items: [{ to: '/', label: 'Home', icon: Home, exact: true }],
  },
  {
    label: 'PK Analysis',
    items: [
      { to: '/nca', label: 'NCA', icon: LineChart, exact: true },
      { to: '/nca/sparse', label: 'Sparse NCA', icon: ScatterChart },
      { to: '/bayes/map', label: 'MAP Individual PK', icon: Brain },
      { to: '/sim', label: 'Simulation', icon: FlaskConical },
    ],
  },
  {
    label: 'Formulation & BE',
    items: [
      { to: '/dissolution', label: 'Dissolution', icon: Waves },
      { to: '/ivivc', label: 'IVIVC', icon: Activity },
      { to: '/be', label: 'Bioequivalence', icon: Scale },
      { to: '/be/anova', label: 'Formal BE ANOVA', icon: Scale },
      { to: '/be/rsabe', label: 'FDA RSABE', icon: Sigma },
      { to: '/supac', label: 'SUPAC & Alcohol', icon: ShieldCheck },
    ],
  },
  {
    label: 'Workflow',
    items: [{ to: '/pipeline', label: 'Study Pipeline', icon: Workflow }],
  },
]

const COLLAPSED_KEY = 'openpkflow.sidebar.collapsed'

export function Sidebar({
  mobileOpen,
  onClose,
}: {
  mobileOpen?: boolean
  onClose?: () => void
}) {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem(COLLAPSED_KEY) === '1'
    } catch {
      return false
    }
  })

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      try {
        window.localStorage.setItem(COLLAPSED_KEY, c ? '0' : '1')
      } catch {
        /* storage unavailable */
      }
      return !c
    })
  }

  return (
    <aside
      className={cn(
        'bg-surface border-r border-border flex flex-col shrink-0 transition-all duration-300',
        collapsed ? 'lg:w-[60px]' : 'lg:w-[220px]',
        'w-[220px]',
        'max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-50 max-lg:w-[220px]',
        mobileOpen ? 'max-lg:translate-x-0' : 'max-lg:-translate-x-full',
        'max-md:shadow-xl',
      )}
    >
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-border">
        <div className={cn('flex items-center gap-2.5 min-w-0', collapsed && 'lg:justify-center lg:w-full lg:px-0')}>
          <div className="font-mono-ui w-7 h-7 shrink-0 rounded-sm bg-accent flex items-center justify-center text-accent-fg font-bold text-sm">
            PK
          </div>
          <span
            className={cn(
              'font-semibold text-[15.5px] text-text tracking-tight truncate',
              collapsed && 'lg:hidden',
            )}
          >
            OpenPKFlow
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="lg:hidden p-2 rounded-sm text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="flex-1 py-3 flex flex-col gap-0.5 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-1.5">
            <div
              className={cn(
                'font-mono-ui px-4 pb-1.5 pt-2 text-[11px] uppercase tracking-[0.16em] text-text-dim',
                collapsed && 'lg:hidden',
              )}
            >
              {group.label}
            </div>
            {collapsed && (
              <div className="mx-3 my-2 hidden border-t border-border lg:block" aria-hidden="true" />
            )}
            {group.items.map(({ to, label, icon: Icon, exact }) => (
              <NavLink
                key={to}
                to={to}
                end={exact}
                onClick={onClose}
                title={collapsed ? label : undefined}
                aria-label={collapsed ? label : undefined}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2.5 px-4 py-2 border-l-[3px] text-[14.5px] font-medium transition-all duration-150',
                    collapsed && 'lg:justify-center lg:px-0 lg:mx-1.5 lg:border-l-0 lg:rounded-sm',
                    isActive
                      ? 'bg-surface-2 text-text border-l-accent'
                      : 'text-text-muted hover:text-text hover:bg-surface-2 border-l-transparent',
                    collapsed && isActive && 'lg:bg-accent-muted lg:text-accent',
                  )
                }
              >
                <Icon size={15} aria-hidden="true" className="shrink-0" />
                <span className={cn('truncate', collapsed && 'lg:hidden')}>{label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <button
        type="button"
        onClick={toggleCollapsed}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        className="hidden lg:flex items-center justify-center gap-2 border-t border-border px-4 py-2.5 text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
      >
        {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        {!collapsed && <span className="text-xs font-medium">Collapse</span>}
      </button>

      <div
        className={cn('mt-auto border-t border-border px-4 py-3', collapsed && 'lg:hidden')}
      >
          <p className="font-mono-ui text-[10px] uppercase tracking-[0.12em] text-text-dim">
            Priyam Thakar
          </p>
          <a
            href="mailto:priyamthakar1@gmail.com"
            className="mt-1 flex items-center gap-1.5 text-[11px] text-accent no-underline hover:text-accent-hover"
          >
            <Mail size={12} aria-hidden="true" />
            priyamthakar1@gmail.com
          </a>
          <p className="font-mono-ui mt-3 text-xs text-text-dim">Open-source / MIT</p>
      </div>
    </aside>
  )
}
