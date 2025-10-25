import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { useKV } from '@github/spark/hooks'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [user, setUser] = useKV<{ username: string } | null>('synapse-user', null)
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (username.trim()) {
      setUser({ username: username.trim() })
      navigate('/search')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-secondary/10" />
      
      <Card className="glass-panel neon-glow max-w-md w-full p-8 relative z-10">
        <div className="text-center mb-8">
          <h1 className="font-mono font-bold text-4xl bg-gradient-to-r from-electric-purple via-hot-pink to-cyan bg-clip-text text-transparent mb-2">
            SYNAPSE
          </h1>
          <p className="text-muted-foreground text-sm tracking-wide">
            Learn From Minds You Trust
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-foreground mb-2">
              Username
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              className="neon-glow-hover bg-input/50"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
              Password
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="neon-glow-hover bg-input/50"
              required
            />
          </div>

          <Button
            type="submit"
            className="w-full bg-primary hover:bg-primary/90 neon-glow text-primary-foreground font-semibold"
          >
            {isCreating ? 'Create Account' : 'Sign In'}
          </Button>

          <button
            type="button"
            onClick={() => setIsCreating(!isCreating)}
            className="w-full text-sm text-muted-foreground hover:text-primary transition-colors"
          >
            {isCreating ? 'Already have an account? Sign in' : 'Need an account? Create one'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-border">
          <p className="text-xs text-center text-muted-foreground">
            Semantic search platform for TikTok transcripts
          </p>
        </div>
      </Card>
    </div>
  )
}
