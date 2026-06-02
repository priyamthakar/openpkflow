import { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-bg">
          <div className="text-center max-w-sm px-6">
            <AlertTriangle size={48} className="text-danger mx-auto mb-4" />
            <h1 className="text-xl font-bold text-text mb-2">Something went wrong</h1>
            <p className="text-sm text-text-muted mb-6">
              {this.state.error?.message ?? 'An unexpected error occurred.'}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-sm bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors"
            >
              <RefreshCw size={16} />
              Reload page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
