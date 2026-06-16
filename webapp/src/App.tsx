import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/layout/ThemeProvider'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/layout/ErrorBoundary'
import { PageLoader } from '@/components/layout/PageLoader'

const Home = lazy(() => import('@/pages/Home'))
const NcaPage = lazy(() => import('@/pages/NcaPage'))
const DissolutionPage = lazy(() => import('@/pages/DissolutionPage'))
const SimPage = lazy(() => import('@/pages/SimPage'))
const IvIvcPage = lazy(() => import('@/pages/IvIvcPage'))
const BePage = lazy(() => import('@/pages/BePage'))
const NotFound = lazy(() => import('@/pages/NotFound'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
})

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter basename={import.meta.env.BASE_URL}>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route element={<AppShell />}>
                  <Route index element={<Home />} />
                  <Route path="nca" element={<NcaPage />} />
                  <Route path="dissolution" element={<DissolutionPage />} />
                  <Route path="sim" element={<SimPage />} />
                  <Route path="ivivc" element={<IvIvcPage />} />
                  <Route path="be" element={<BePage />} />
                  <Route path="*" element={<NotFound />} />
                </Route>
              </Routes>
            </Suspense>
          </BrowserRouter>
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}
