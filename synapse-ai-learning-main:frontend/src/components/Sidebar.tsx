import { NavLink } from 'react-router-dom'
import { Books, MagnifyingGlass, Article, ChartBar, UploadSimple } from '@phosphor-icons/react'
import { Sparkles, FlaskConical } from 'lucide-react' // Hermes Phase 0
import { cn } from '@/lib/utils'

// Hermes Phase 0 - Feature flags
const HERMES_ENABLED = import.meta.env.VITE_HERMES_ENABLED !== 'false'
const LABS_ENABLED = import.meta.env.VITE_LABS_ENABLED === 'true'

const navItems = [
  { icon: Books, label: 'Library', path: '/library' },
  { icon: MagnifyingGlass, label: 'Search', path: '/search' },
  { icon: Article, label: 'Transcripts', path: '/transcripts' },
  { icon: ChartBar, label: 'Dashboard', path: '/dashboard' },
  { icon: UploadSimple, label: 'Ingest', path: '/ingest' },
]

// Hermes Phase 0 - Conditional Hermes nav item
const hermesNavItems = HERMES_ENABLED ? [
  { icon: Sparkles, label: 'Hermes', path: '/hermes', iconType: 'lucide' as const },
] : []

// Hermes Phase 0 - Conditional Labs nav items
const labsNavItems = LABS_ENABLED ? [
  { icon: FlaskConical, label: 'Labs', path: '/labs/dashboard', iconType: 'lucide' as const, experimental: true },
] : []

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 glass-panel border-r border-primary/20 hidden lg:flex flex-col">
      <div className="p-6 border-b border-primary/20">
        <h1 className="font-mono font-bold text-2xl bg-gradient-to-r from-electric-purple to-hot-pink bg-clip-text text-transparent">
          SYNAPSE
        </h1>
        <p className="text-xs text-muted-foreground mt-1 tracking-wide">
          Learn From Minds You Trust
        </p>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                'hover:bg-primary/10 hover:neon-glow-hover',
                isActive
                  ? 'bg-primary/20 text-primary neon-glow border border-primary/30'
                  : 'text-muted-foreground border border-transparent'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon size={20} weight={isActive ? 'fill' : 'regular'} />
                <span className="font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
        
        {/* Hermes Phase 0 - Hermes section */}
        {hermesNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                'hover:bg-primary/10 hover:neon-glow-hover',
                isActive
                  ? 'bg-primary/20 text-primary neon-glow border border-primary/30'
                  : 'text-muted-foreground border border-transparent'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon size={20} className={isActive ? 'fill-current' : ''} />
                <span className="font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
        
        {/* Hermes Phase 0 - Labs section */}
        {labsNavItems.length > 0 && (
          <div className="pt-4 mt-4 border-t border-primary/10">
            <p className="text-xs text-muted-foreground px-4 mb-2">Experimental</p>
            {labsNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                    'hover:bg-amber-500/10 hover:border-amber-500/20',
                    isActive
                      ? 'bg-amber-500/20 text-amber-500 border border-amber-500/30'
                      : 'text-muted-foreground border border-transparent'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <item.icon size={20} className={isActive ? 'fill-current' : ''} />
                    <span className="font-medium">{item.label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </div>
        )}
      </nav>

      <div className="p-4 border-t border-primary/20 text-xs text-muted-foreground">
        <p>Semantic Search Platform</p>
        <p className="font-mono mt-1">v1.0.0</p>
      </div>
    </aside>
  )
}

export function MobileNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 glass-panel border-t border-primary/20 lg:hidden">
      <div className="flex items-center justify-around p-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-all',
                isActive ? 'text-primary' : 'text-muted-foreground'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon size={24} weight={isActive ? 'fill' : 'regular'} />
                <span className="text-xs font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
