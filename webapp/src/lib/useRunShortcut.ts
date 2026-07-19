import { useEffect } from 'react'

/**
 * Runs `onRun` when the user presses Ctrl+Enter (or Cmd+Enter on macOS)
 * anywhere outside a text-editing field, as long as `enabled` is true.
 */
export function useRunShortcut(onRun: () => void, enabled: boolean) {
  useEffect(() => {
    if (!enabled) return
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Enter' || (!event.ctrlKey && !event.metaKey)) return
      const target = event.target as HTMLElement | null
      const tag = target?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target?.isContentEditable) {
        return
      }
      event.preventDefault()
      onRun()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onRun, enabled])
}
