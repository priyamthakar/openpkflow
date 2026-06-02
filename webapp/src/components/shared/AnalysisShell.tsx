import { Children, useEffect, useRef, useState, type ReactNode } from 'react'
import { GripVertical } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  children?: ReactNode
  left?: ReactNode
  right?: ReactNode
  leftWide?: boolean
  resultKey?: string | number | boolean | null
}

export function AnalysisShell({ children, left, right, leftWide, resultKey }: Props) {
  const [leftWidth, setLeftWidth] = useState<number | null>(null)
  const [dragging, setDragging] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const resultRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!resultKey || !resultRef.current) return
    resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [resultKey])

  useEffect(() => {
    if (!dragging) return
    function onMove(event: MouseEvent) {
      const bounds = rootRef.current?.getBoundingClientRect()
      if (!bounds) return
      const next = event.clientX - bounds.left
      const max = Math.min(680, bounds.width - 360)
      setLeftWidth(Math.max(280, Math.min(max, next)))
    }
    function onUp() {
      setDragging(false)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [dragging])

  const childPanels = Children.toArray(children)
  const leftPanel = left ?? childPanels[0]
  const rightPanel = right ?? childPanels[1]
  const resolvedLeftWidth = leftWidth ?? (leftWide ? 520 : 320)

  return (
    <div
      ref={rootRef}
      className="flex-1 overflow-hidden p-5 md:p-6"
      style={{ cursor: dragging ? 'col-resize' : undefined }}
    >
      <div className="flex h-full min-h-0 flex-col gap-5 md:flex-row">
        <aside
          className="min-h-0 shrink-0 overflow-y-auto pr-0 md:pr-1"
          style={{ width: `min(100%, ${resolvedLeftWidth}px)` }}
        >
          {leftPanel}
        </aside>

        <button
          type="button"
          aria-label="Resize analysis panels"
          onMouseDown={() => setDragging(true)}
          className={cn(
            'hidden md:flex w-4 shrink-0 items-center justify-center rounded-sm border border-border',
            'bg-surface-2 text-text-muted hover:text-text hover:border-border-2',
          )}
        >
          <GripVertical size={14} />
        </button>

        <main ref={resultRef} className="min-h-0 min-w-0 flex-1 overflow-y-auto pl-0 md:pl-1">
          {rightPanel}
        </main>
      </div>
    </div>
  )
}
