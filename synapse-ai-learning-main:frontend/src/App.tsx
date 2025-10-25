import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Sidebar, MobileNav } from '@/components/Sidebar'
import { SearchPage } from '@/pages/SearchPage'
import { LibraryPage } from '@/pages/LibraryPage'
import { CreatorDetailPage } from '@/pages/CreatorDetailPage'
import { TranscriptsPage } from '@/pages/TranscriptsPage'
import { TranscriptPage } from '@/pages/TranscriptPage'
import { DashboardPage } from '@/pages/DashboardPage'
import IngestPage from '@/pages/IngestPage'
// Hermes Phase 0
import { HermesLanding } from '@/pages/HermesLanding'
import { AnalyzePage } from '@/pages/AnalyzePage'
import { PlanPage } from '@/pages/PlanPage'
import { LabsDashboard } from '@/pages/LabsDashboard'

// Hermes Phase 0 - Feature flags
const LABS_ENABLED = import.meta.env.VITE_LABS_ENABLED === 'true'

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <MobileNav />
      <main className="lg:ml-64 p-6 lg:p-8 pb-24 lg:pb-8">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          classNames: {
            toast: 'glass-panel border-primary/20',
            title: 'text-foreground',
            description: 'text-muted-foreground',
          },
        }}
      />
      
      <Routes>
        <Route
          path="/search"
          element={
            <AppLayout>
              <SearchPage />
            </AppLayout>
          }
        />
        
        <Route
          path="/library"
          element={
            <AppLayout>
              <LibraryPage />
            </AppLayout>
          }
        />
        
        <Route
          path="/creator/:username"
          element={
            <AppLayout>
              <CreatorDetailPage />
            </AppLayout>
          }
        />
        
        <Route
          path="/transcripts"
          element={
            <AppLayout>
              <TranscriptsPage />
            </AppLayout>
          }
        />
        
        <Route
          path="/transcript/:username/:videoId"
          element={
            <AppLayout>
              <TranscriptPage />
            </AppLayout>
          }
        />
        
        <Route
          path="/dashboard"
          element={
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          }
        />
        
        <Route
          path="/ingest"
          element={
            <AppLayout>
              <IngestPage />
            </AppLayout>
          }
        />
        
        {/* Hermes Phase 0 - Hermes routes */}
        <Route
          path="/hermes"
          element={
            <AppLayout>
              <HermesLanding />
            </AppLayout>
          }
        />
        
        <Route
          path="/hermes/analyze"
          element={
            <AppLayout>
              <AnalyzePage />
            </AppLayout>
          }
        />
        
        <Route
          path="/hermes/plan/:planId"
          element={
            <AppLayout>
              <PlanPage />
            </AppLayout>
          }
        />
        
        {/* Hermes Phase 0 - Labs routes (conditional) */}
        {LABS_ENABLED && (
          <Route
            path="/labs/dashboard"
            element={
              <AppLayout>
                <LabsDashboard />
              </AppLayout>
            }
          />
        )}
        
        <Route path="/" element={<Navigate to="/search" replace />} />
        <Route path="*" element={<Navigate to="/search" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App