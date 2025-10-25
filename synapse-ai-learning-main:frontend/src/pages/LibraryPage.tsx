import { useState, useEffect } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { CreatorCard } from '@/components/CreatorCard'
import { EmptyState } from '@/components/EmptyState'
import { Input } from '@/components/ui/input'
import { MagnifyingGlass } from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { Creator } from '@/lib/types'
import { toast } from 'sonner'

export function LibraryPage() {
  const [creators, setCreators] = useState<Creator[]>([])
  const [filteredCreators, setFilteredCreators] = useState<Creator[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadCreators()
  }, [])

  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = creators.filter((creator) =>
        creator.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        creator.category?.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredCreators(filtered)
    } else {
      setFilteredCreators(creators)
    }
  }, [searchQuery, creators])

  const loadCreators = async () => {
    setIsLoading(true)
    try {
      const data = await api.getCreators()
      setCreators(data)
      setFilteredCreators(data)
    } catch (error) {
      toast.error('Failed to load creators')
      console.error('Error loading creators:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel neon-glow p-8 rounded-xl">
        <h1 className="font-mono font-bold text-3xl mb-2 bg-gradient-to-r from-cyan to-neon-blue bg-clip-text text-transparent">
          CREATOR LIBRARY
        </h1>
        <p className="text-muted-foreground mb-6">
          Browse all ingested TikTok creators and their content.
        </p>

        <div className="relative">
          <MagnifyingGlass
            size={20}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            id="library-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search creators..."
            className="pl-10 neon-glow-hover bg-input/50"
          />
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-64 glass-panel" />
          ))}
        </div>
      )}

      {!isLoading && filteredCreators.length === 0 && (
        <EmptyState message="No creators found. Try a different search." />
      )}

      {!isLoading && filteredCreators.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">
              {filteredCreators.length} {filteredCreators.length === 1 ? 'Creator' : 'Creators'}
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCreators.map((creator) => (
              <CreatorCard key={creator.username} creator={creator} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
