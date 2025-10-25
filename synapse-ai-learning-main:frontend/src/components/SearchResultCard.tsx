import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CaretRight } from '@phosphor-icons/react'
import type { SearchResult } from '@/lib/types'
import { useNavigate } from 'react-router-dom'

interface SearchResultCardProps {
  result: SearchResult
  searchQuery?: string
}

export function SearchResultCard({ result, searchQuery }: SearchResultCardProps) {
  const navigate = useNavigate()

  const handleOpenTranscript = () => {
    // Pass the search query to highlight ALL matching segments in the transcript
    const query = searchQuery || result.snippet || ''
    navigate(`/transcript/${result.username}/${result.video_id}?query=${encodeURIComponent(query)}`)
  }

  return (
    <Card className="glass-panel neon-glow-hover p-5 transition-all duration-200 hover:border-primary/40">
      <div className="mb-3">
        <p className="text-foreground leading-relaxed">{result.snippet}</p>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3 text-sm">
          <Badge variant="secondary" className="bg-secondary/20 text-cyan border-secondary/40">
            @{result.username}
          </Badge>
          <span className="font-mono text-muted-foreground">{result.video_id}</span>
          <span className="font-mono text-primary font-semibold">{result.timestamp}</span>
        </div>

        <Button
          onClick={handleOpenTranscript}
          size="sm"
          className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 neon-glow-hover"
        >
          <CaretRight size={16} weight="bold" className="mr-1" />
          Open At Timestamp
        </Button>
      </div>
    </Card>
  )
}
