import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card } from '@/components/ui/card'
import type { TranscriptSegment } from '@/lib/types'
import { cn } from '@/lib/utils'

interface TranscriptViewerProps {
  segments: TranscriptSegment[]
  onTimestampClick?: (timestamp: string) => void
}

export function TranscriptViewer({ segments, onTimestampClick }: TranscriptViewerProps) {
  const firstHighlightRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Scroll to first highlighted segment on load
    if (firstHighlightRef.current) {
      firstHighlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [segments])

  let firstHighlightSet = false

  return (
    <ScrollArea className="h-[calc(100vh-12rem)]">
      <div className="space-y-1">
        {segments.map((segment, index) => {
          const isHighlighted = segment.highlighted || false
          const isFirstHighlight = isHighlighted && !firstHighlightSet
          if (isFirstHighlight) firstHighlightSet = true

          return (
            <div
              key={index}
              ref={isFirstHighlight ? firstHighlightRef : null}
              className={cn(
                'group flex gap-4 p-3 rounded-lg transition-all duration-300',
                isHighlighted && 'highlight-match neon-glow bg-primary/10 border border-primary/30'
              )}
            >
              <button
                onClick={() => onTimestampClick?.(segment.timestamp)}
                className="font-mono text-sm text-primary hover:text-hot-pink transition-colors font-semibold shrink-0 cursor-pointer"
              >
                {segment.timestamp}
              </button>
              <p className={cn(
                "leading-relaxed flex-1",
                isHighlighted ? "text-foreground font-medium" : "text-muted-foreground"
              )}>
                {segment.text}
              </p>
            </div>
          )
        })}
      </div>
    </ScrollArea>
  )
}
