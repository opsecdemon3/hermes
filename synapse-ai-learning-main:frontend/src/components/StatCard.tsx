import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface StatCardProps {
  label: string
  value: string | number
  icon?: React.ReactNode
  className?: string
}

export function StatCard({ label, value, icon, className }: StatCardProps) {
  return (
    <Card className={cn('glass-panel neon-glow-hover p-6 transition-all duration-200', className)}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-sm text-muted-foreground uppercase tracking-wide">{label}</p>
        {icon && <div className="text-primary">{icon}</div>}
      </div>
      <p className="text-3xl font-bold font-mono bg-gradient-to-r from-cyan to-primary bg-clip-text text-transparent">
        {value}
      </p>
    </Card>
  )
}
