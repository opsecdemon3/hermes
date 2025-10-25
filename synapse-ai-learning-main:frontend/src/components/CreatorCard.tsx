import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Video } from '@phosphor-icons/react'
import type { Creator } from '@/lib/types'
import { useNavigate } from 'react-router-dom'

interface CreatorCardProps {
  creator: Creator
}

export function CreatorCard({ creator }: CreatorCardProps) {
  const navigate = useNavigate()

  return (
    <Card
      className="glass-panel neon-glow-hover cursor-pointer transition-all duration-200 hover:scale-[1.02] p-6"
      onClick={() => navigate(`/creator/${creator.username}`)}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-cyan">@{creator.username}</h3>
          {creator.category && (
            <Badge variant="secondary" className="mt-2 bg-secondary/20 text-secondary border-secondary/40">
              {creator.category}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Video size={18} />
          <span className="font-mono text-sm">{creator.video_count}</span>
        </div>
      </div>

      {creator.top_topics && creator.top_topics.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {creator.top_topics.slice(0, 5).map((topic) => (
            <Badge key={topic} variant="outline" className="text-xs border-primary/30 text-foreground">
              {topic}
            </Badge>
          ))}
        </div>
      )}

      {creator.last_updated && (
        <p className="text-xs text-muted-foreground font-mono">
          Updated: {new Date(creator.last_updated).toLocaleDateString()}
        </p>
      )}

      <Button
        variant="ghost"
        size="sm"
        className="w-full mt-4 text-primary hover:bg-primary/10"
        onClick={(e) => {
          e.stopPropagation()
          navigate(`/creator/${creator.username}`)
        }}
      >
        View Details
      </Button>
    </Card>
  )
}
