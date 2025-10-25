// Hermes Phase 0
/**
 * HermesLanding - Landing page for Hermes content strategy planner
 */

import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Sparkles, Target, TrendingUp } from 'lucide-react'

export function HermesLanding() { // Hermes Phase 0
  const navigate = useNavigate()

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary">
          <Sparkles className="w-4 h-4" />
          <span className="text-sm font-medium">AI-Powered Content Strategy</span>
        </div>
        
        <h1 className="text-4xl font-bold tracking-tight">
          Welcome to Hermes
        </h1>
        
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Turn your content into a strategic growth engine. Hermes analyzes top-performing 
          creators and generates personalized content plans tailored to your goals.
        </p>
        
        <Button 
          size="lg" 
          onClick={() => navigate('/hermes/analyze')}
          className="mt-4"
        >
          Create Your First Plan
        </Button>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <Card>
          <CardHeader>
            <Target className="w-8 h-8 text-primary mb-2" />
            <CardTitle>Goal-Driven</CardTitle>
            <CardDescription>
              Choose your objective: Growth, Leads, or Sales
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Every plan is customized to your specific business goal, 
              ensuring maximum impact.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Sparkles className="w-8 h-8 text-primary mb-2" />
            <CardTitle>Pattern Detection</CardTitle>
            <CardDescription>
              Learn from the best performers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Hermes analyzes winning content patterns and shows you 
              exactly what works.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <TrendingUp className="w-8 h-8 text-primary mb-2" />
            <CardTitle>Actionable Plans</CardTitle>
            <CardDescription>
              Day-by-day content roadmap
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Get detailed outlines, hooks, CTAs, and receipts backing 
              every recommendation.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* CTA */}
      <Card className="border-primary/20 bg-primary/5 mt-12">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <h2 className="text-2xl font-semibold">Ready to get started?</h2>
            <p className="text-muted-foreground">
              Provide a creator handle or paste video links to begin analyzing.
            </p>
            <Button onClick={() => navigate('/hermes/analyze')}>
              Start Analyzing
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
