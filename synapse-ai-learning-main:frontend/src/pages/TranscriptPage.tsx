import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { TranscriptViewer } from '@/components/TranscriptViewer'
import { ArrowLeft, Play } from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { Transcript } from '@/lib/types'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

export function TranscriptPage() {
  const { username, videoId } = useParams<{ username: string; videoId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [transcript, setTranscript] = useState<Transcript | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const searchQuery = searchParams.get('query') || undefined

  useEffect(() => {
    if (username && videoId) {
      loadTranscript()
    }
  }, [username, videoId, searchQuery])

  const loadTranscript = async () => {
    if (!username || !videoId) return

    setIsLoading(true)
    try {
      const data = await api.getTranscript(username, videoId, searchQuery)
      setTranscript(data)
    } catch (error) {
      toast.error('Failed to load transcript')
      console.error('Error loading transcript:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleTimestampClick = (timestamp: string) => {
    // Scroll to timestamp in the transcript (handled by TranscriptViewer)
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel neon-glow p-6 rounded-xl">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-4 text-muted-foreground hover:text-primary"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back
        </Button>

        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="font-mono font-bold text-2xl mb-2 text-cyan">
              @{username}
            </h1>
            <p className="text-muted-foreground font-mono text-sm">
              Video ID: {videoId}
            </p>
          </div>

          <Button
            variant="outline"
            className="border-primary/40 text-primary hover:bg-primary/10 neon-glow-hover"
          >
            <Play size={18} weight="fill" className="mr-2" />
            Watch Video
          </Button>
        </div>
      </div>

      {isLoading ? (
        <Skeleton className="h-[600px] glass-panel" />
      ) : transcript ? (
        <Card className="glass-panel p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Transcript</h2>
            {searchQuery && transcript.highlighted_count && transcript.highlighted_count > 0 && (
              <span className="text-sm text-primary font-mono">
                {transcript.highlighted_count} relevant {transcript.highlighted_count === 1 ? 'segment' : 'segments'} highlighted
              </span>
            )}
          </div>
          <TranscriptViewer
            segments={transcript.segments}
            onTimestampClick={handleTimestampClick}
          />
        </Card>
      ) : (
        <Card className="glass-panel p-12 text-center">
          <p className="text-muted-foreground">Transcript not found</p>
        </Card>
      )}
    </div>
  )
}
