import { Sun, Moon } from 'lucide-react'
import { useTheme } from './theme-context'
import { cn } from '@/lib/utils'

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme()

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      className={cn(
        'p-2 rounded-sm text-text-muted hover:text-text hover:bg-surface-2 transition-colors',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40',
        className,
      )}
    >
      {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
    </button>
  )
}
