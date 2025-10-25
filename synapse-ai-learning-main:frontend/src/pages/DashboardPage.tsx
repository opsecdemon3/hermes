import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { StatCard } from '@/components/StatCard'
import { Card } from '@/components/ui/card'
import { Database, Users, FileText, ArrowsClockwise } from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { SystemStatus } from '@/lib/types'
import { toast } from 'sonner'

export function DashboardPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isVerifying, setIsVerifying] = useState(false)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    setIsLoading(true)
    try {
      const data = await api.getSystemStatus()
      setStatus(data)
    } catch (error) {
      toast.error('Failed to load system status')
      console.error('Error loading status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReverify = async () => {
    setIsVerifying(true)
    try {
      const data = await api.reverifySystem()
      setStatus(data)
      toast.success('System reverified successfully')
    } catch (error) {
      toast.error('Failed to reverify system')
      console.error('Error reverifying system:', error)
    } finally {
      setIsVerifying(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel neon-glow p-8 rounded-xl">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="font-mono font-bold text-3xl mb-2 bg-gradient-to-r from-hot-pink to-electric-purple bg-clip-text text-transparent">
              SYSTEM DASHBOARD
            </h1>
            <p className="text-muted-foreground">
              Monitor system health and data coverage.
            </p>
          </div>

          <Button
            onClick={handleReverify}
            disabled={isVerifying}
            className="bg-primary hover:bg-primary/90 neon-glow"
          >
            <ArrowsClockwise size={18} className="mr-2" weight={isVerifying ? 'bold' : 'regular'} />
            {isVerifying ? 'Verifying...' : 'Re-verify System'}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32 glass-panel" />
          ))}
        </div>
      ) : status ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              label="Total Creators"
              value={status.total_creators}
              icon={<Users size={24} weight="duotone" />}
            />
            <StatCard
              label="Total Transcripts"
              value={status.total_transcripts}
              icon={<FileText size={24} weight="duotone" />}
            />
            <StatCard
              label="Indexed Vectors"
              value={status.total_vectors.toLocaleString()}
              icon={<Database size={24} weight="duotone" />}
            />
            <StatCard
              label="System Status"
              value={status.status}
              className={status.status === 'healthy' ? 'border-green-500/30' : ''}
            />
          </div>

          <Card className="glass-panel p-6">
            <h3 className="text-lg font-semibold mb-4 text-foreground">System Information</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Status</span>
                <span className="font-mono font-semibold text-primary uppercase">{status.status}</span>
              </div>
              {status.timestamp && (
                <div className="flex items-center justify-between py-2 border-b border-border">
                  <span className="text-muted-foreground">Last Verified</span>
                  <span className="font-mono text-sm text-foreground">
                    {new Date(status.timestamp).toLocaleString()}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Avg Vectors per Transcript</span>
                <span className="font-mono text-foreground">
                  {status.total_transcripts > 0
                    ? Math.round(status.total_vectors / status.total_transcripts)
                    : 0}
                </span>
              </div>
            </div>
          </Card>
        </>
      ) : (
        <Card className="glass-panel p-12 text-center">
          <p className="text-muted-foreground">Failed to load system status</p>
        </Card>
      )}
    </div>
  )
}
