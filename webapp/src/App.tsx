import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/layout/ThemeProvider'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/layout/ErrorBoundary'
import { PageLoader } from '@/components/layout/PageLoader'

const Home = lazy(() => import('@/pages/Home'))
const NcaPage = lazy(() => import('@/pages/NcaPage'))
const SparseNcaPage = lazy(() => import('@/pages/SparseNcaPage'))
const DissolutionPage = lazy(() => import('@/pages/DissolutionPage'))
const SimPage = lazy(() => import('@/pages/SimPage'))
const IvIvcPage = lazy(() => import('@/pages/IvIvcPage'))
const BePage = lazy(() => import('@/pages/BePage'))
const FormalBePage = lazy(() => import('@/pages/FormalBePage'))
const PipelinePage = lazy(() => import('@/pages/PipelinePage'))
const MapPkPage = lazy(() => import('@/pages/MapPkPage'))
const SupacPage = lazy(() => import('@/pages/SupacPage'))
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
                  <Route path="nca/sparse" element={<SparseNcaPage />} />
                  <Route path="dissolution" element={<DissolutionPage />} />
                  <Route path="sim" element={<SimPage />} />
                  <Route path="ivivc" element={<IvIvcPage />} />
                  <Route path="be" element={<BePage />} />
                  <Route path="be/anova" element={<FormalBePage />} />
                  <Route path="pipeline" element={<PipelinePage />} />
                  <Route path="bayes/map" element={<MapPkPage />} />
                  <Route path="supac" element={<SupacPage />} />
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
