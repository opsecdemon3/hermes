// Hermes Phase 0
/**
 * AnalyzePage - Form to submit plan generation request
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { Loader2, Sparkles } from 'lucide-react'

// Hermes Phase 0 - Feature flag check
const HERMES_ENABLED = import.meta.env.VITE_HERMES_ENABLED !== 'false'

type Goal = 'GROWTH' | 'LEADS' | 'SALES' // Hermes Phase 0

interface PlanRequest { // Hermes Phase 0
  handle?: string
  links?: string[]
  goal: Goal
}

export function AnalyzePage() { // Hermes Phase 0
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [inputMode, setInputMode] = useState<'handle' | 'links'>('handle')
  const [handle, setHandle] = useState('')
  const [linksText, setLinksText] = useState('')
  const [goal, setGoal] = useState<Goal>('GROWTH')

  if (!HERMES_ENABLED) { // Hermes Phase 0
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Hermes Not Enabled</CardTitle>
            <CardDescription>
              The Hermes feature is currently disabled. Contact your administrator.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => { // Hermes Phase 0
    e.preventDefault()
    setLoading(true)

    try {
      // Hermes Phase 0 - Build request payload
      const payload: PlanRequest = { goal }
      
      if (inputMode === 'handle') {
        if (!handle.trim()) {
          toast.error('Please enter a creator handle')
          setLoading(false)
          return
        }
        payload.handle = handle.trim()
      } else {
        const links = linksText
          .split('\n')
          .map(l => l.trim())
          .filter(l => l.length > 0)
        
        if (links.length === 0) {
          toast.error('Please enter at least one video link')
          setLoading(false)
          return
        }
        payload.links = links
      }

      // Hermes Phase 0 - Call API
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE}/api/hermes/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer stub_token` // Hermes Phase 0 - stub auth
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail?.message || 'Failed to submit plan')
      }

      const data = await response.json()
      
      toast.success('Plan queued successfully!')
      navigate(`/hermes/plan/${data.plan_id}`)
      
    } catch (error) {
      console.error('Plan submission error:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to submit plan')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-primary" />
          Analyze Content
        </h1>
        <p className="text-muted-foreground mt-2">
          Start by providing a creator to analyze or specific video links
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Content Input</CardTitle>
          <CardDescription>
            Choose how you want to provide content for analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Input Mode Tabs */}
            <Tabs value={inputMode} onValueChange={(v) => setInputMode(v as 'handle' | 'links')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="handle">Creator Handle</TabsTrigger>
                <TabsTrigger value="links">Video Links</TabsTrigger>
              </TabsList>
              
              <TabsContent value="handle" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="handle">TikTok Handle</Label>
                  <Input
                    id="handle"
                    placeholder="@creator_username"
                    value={handle}
                    onChange={(e) => setHandle(e.target.value)}
                    disabled={loading}
                  />
                  <p className="text-sm text-muted-foreground">
                    Enter the creator's TikTok handle (with or without @)
                  </p>
                </div>
              </TabsContent>
              
              <TabsContent value="links" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="links">Video Links</Label>
                  <Textarea
                    id="links"
                    placeholder="https://tiktok.com/@user/video/123&#10;https://tiktok.com/@user/video/456"
                    value={linksText}
                    onChange={(e) => setLinksText(e.target.value)}
                    disabled={loading}
                    rows={5}
                  />
                  <p className="text-sm text-muted-foreground">
                    One link per line. Paste TikTok video URLs to analyze.
                  </p>
                </div>
              </TabsContent>
            </Tabs>

            {/* Goal Selection */}
            <div className="space-y-2">
              <Label htmlFor="goal">Content Goal</Label>
              <Select value={goal} onValueChange={(v) => setGoal(v as Goal)} disabled={loading}>
                <SelectTrigger id="goal">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GROWTH">Growth (Followers & Reach)</SelectItem>
                  <SelectItem value="LEADS">Leads (Email & Contact)</SelectItem>
                  <SelectItem value="SALES">Sales (Conversions)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                What's your primary objective for this content strategy?
              </p>
            </div>

            {/* Submit */}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Plan
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
