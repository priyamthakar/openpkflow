import { SearchX } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 py-20">
      <SearchX size={48} className="text-text-dim mb-5" />
      <h1 className="text-2xl font-bold text-text mb-2">Page not found</h1>
      <p className="text-text-muted mb-6 max-w-sm">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-sm bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors no-underline"
      >
        Go back home
      </Link>
    </div>
  )
}
