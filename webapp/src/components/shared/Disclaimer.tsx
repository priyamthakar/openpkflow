import { Info } from 'lucide-react'

export function Disclaimer({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 rounded-sm border border-warning/20 bg-warning/5 px-4 py-3 text-warning text-xs leading-relaxed">
      <Info size={14} className="mt-0.5 shrink-0" />
      <p>{text}</p>
    </div>
  )
}
