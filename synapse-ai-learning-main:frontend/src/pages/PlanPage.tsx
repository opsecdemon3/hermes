// Hermes Phase 0
/**
 * PlanPage - View and poll plan status
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Loader2, CheckCircle2, XCircle, Clock, Download, ArrowLeft } from 'lucide-react'

// Hermes Phase 0 - Type definitions
type PlanStatus = 'queued' | 'running' | 'ready' | 'failed' // Hermes Phase 0
type Goal = 'GROWTH' | 'LEADS' | 'SALES' // Hermes Phase 0

interface PlanItem { // Hermes Phase 0
  day_index: number
  hook: string
  outline: string[]
  cta: string
  length_s: number
  receipts: Array<{ video_id?: string; start?: number; end?: number }>
}

interface PlanEnvelope { // Hermes Phase 0
  plan_id: string
  status: PlanStatus
  goal: Goal
  summary?: Record<string, any>
  items?: PlanItem[]
  pdf_signed_url?: string
  meta: {
    source_type: 'handle' | 'links'
    inputs: Record<string, any>
    created_at: string
  }
}

export function PlanPage() { // Hermes Phase 0
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()
  const [plan, setPlan] = useState<PlanEnvelope | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPlan = async () => { // Hermes Phase 0
    if (!planId) return

    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE}/api/hermes/plans/${planId}`, {
        headers: {
          'Authorization': `Bearer stub_token` // Hermes Phase 0 - stub auth
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch plan')
      }

      const data = await response.json()
      setPlan(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      toast.error('Failed to load plan')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { // Hermes Phase 0
    fetchPlan()
    
    // Hermes Phase 0 - Poll every 2s if not in terminal state
    const interval = setInterval(() => {
      if (plan?.status === 'queued' || plan?.status === 'running') {
        fetchPlan()
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [planId, plan?.status])

  if (loading) { // Hermes Phase 0
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="pt-6 flex items-center justify-center min-h-[400px]">
            <div className="text-center space-y-4">
              <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
              <p className="text-muted-foreground">Loading plan...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !plan) { // Hermes Phase 0
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-destructive" />
              Error Loading Plan
            </CardTitle>
            <CardDescription>{error || 'Plan not found'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate('/hermes/analyze')}>
              Create New Plan
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const getStatusIcon = () => { // Hermes Phase 0
    switch (plan.status) {
      case 'queued':
        return <Clock className="w-5 h-5 text-yellow-500" />
      case 'running':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
      case 'ready':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-destructive" />
    }
  }

  const getStatusLabel = () => { // Hermes Phase 0
    switch (plan.status) {
      case 'queued': return 'Queued'
      case 'running': return 'Analyzing...'
      case 'ready': return 'Ready'
      case 'failed': return 'Failed'
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/hermes')}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Content Plan</h1>
          <p className="text-muted-foreground">Plan ID: {plan.plan_id}</p>
        </div>
      </div>

      {/* Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon()}
              {getStatusLabel()}
            </CardTitle>
            <Badge variant="secondary">{plan.goal}</Badge>
          </div>
          <CardDescription>
            Created: {new Date(plan.meta.created_at).toLocaleString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {plan.status === 'queued' && (
            <p className="text-muted-foreground">
              Your plan is queued for processing. This usually takes a few minutes.
            </p>
          )}
          {plan.status === 'running' && (
            <p className="text-muted-foreground">
              Analyzing content patterns and generating your personalized plan...
            </p>
          )}
          {plan.status === 'failed' && (
            <div className="space-y-2">
              <p className="text-destructive">
                Plan generation failed. Please try again or contact support.
              </p>
              <Button onClick={() => navigate('/hermes/analyze')}>
                Try Again
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Plan Items (Phase 0: stub) */}
      {plan.items && plan.items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Plan Items</CardTitle>
            <CardDescription>Your {plan.items.length}-day content strategy</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {plan.items.map((item, idx) => (
              <div key={idx}>
                {idx > 0 && <Separator className="my-4" />}
                <div className="space-y-2">
                  <h3 className="font-semibold">Day {item.day_index}</h3>
                  <p className="text-sm text-muted-foreground">{item.hook}</p>
                  <ul className="text-sm list-disc list-inside">
                    {item.outline.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                  <p className="text-sm"><strong>CTA:</strong> {item.cta}</p>
                  <p className="text-xs text-muted-foreground">Length: {item.length_s}s</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* PDF Download (Phase 0: stub) */}
      {plan.pdf_signed_url && (
        <Card>
          <CardContent className="pt-6">
            <Button asChild className="w-full">
              <a href={plan.pdf_signed_url} download>
                <Download className="mr-2 h-4 w-4" />
                Download PDF Plan
              </a>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
