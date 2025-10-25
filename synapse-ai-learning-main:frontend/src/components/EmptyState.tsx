import { Card } from '@/components/ui/card'
import { MagnifyingGlass } from '@phosphor-icons/react'

export function EmptyState({ message }: { message: string }) {
  return (
    <Card className="glass-panel p-12 text-center">
      <MagnifyingGlass size={64} className="mx-auto text-muted-foreground mb-4 opacity-50" />
      <p className="text-lg text-muted-foreground">{message}</p>
    </Card>
  )
}
