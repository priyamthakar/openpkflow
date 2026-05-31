import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { Home } from '@/pages/Home'
import { NcaPage } from '@/pages/NcaPage'
import { DissolutionPage } from '@/pages/DissolutionPage'
import { SimPage } from '@/pages/SimPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Home />} />
            <Route path="nca" element={<NcaPage />} />
            <Route path="dissolution" element={<DissolutionPage />} />
            <Route path="sim" element={<SimPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
