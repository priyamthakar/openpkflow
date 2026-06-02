import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('rounded-sm border border-border bg-surface p-5', className)}>{children}</div>
}
