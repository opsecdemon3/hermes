import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { SearchResultCard } from '@/components/SearchResultCard'
import { SearchFilters } from '@/components/SearchFilters'
import { EmptyState } from '@/components/EmptyState'
import { MagnifyingGlass, Sparkle } from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { SearchResult, SearchFilters as FilterType } from '@/lib/types'
import { toast } from 'sonner'
import { useKV } from '@github/spark/hooks'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [recentSearches, setRecentSearches] = useKV<string[]>('recent-searches', [])
  const [filters, setFilters] = useState<FilterType>({})
  const [filtersOpen, setFiltersOpen] = useState(false)

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setIsLoading(true)
    setHasSearched(true)

    try {
      const searchResults = await api.semanticSearch(searchQuery, filters)
      setResults(searchResults)

      setRecentSearches((current) => {
        const currentSearches = current || []
        const updated = [searchQuery, ...currentSearches.filter(q => q !== searchQuery)].slice(0, 5)
        return updated
      })

      if (searchResults.length === 0) {
        toast.info('No results found. Try adjusting your filters or rephrasing your query.')
      }
    } catch (error) {
      toast.error('Search failed. Please try again.')
      console.error('Search error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleSearch(query)
  }

  const handleClearFilters = () => {
    setFilters({})
    if (query && hasSearched) {
      handleSearch(query)
    }
  }

  // Re-search when filters change (if there's an active search)
  useEffect(() => {
    if (query && hasSearched) {
      handleSearch(query)
    }
  }, [filters])

  return (
    <div className="space-y-6">
      <div className="glass-panel neon-glow p-8 rounded-xl">
        <h1 className="font-mono font-bold text-3xl mb-2 bg-gradient-to-r from-electric-purple to-hot-pink bg-clip-text text-transparent">
          SEMANTIC SEARCH
        </h1>
        <p className="text-muted-foreground mb-6">
          Search ideas, not videos. Find insights across all transcripts.
        </p>

        <form onSubmit={handleSubmit} className="relative">
          <div className="relative">
            <MagnifyingGlass
              size={24}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-primary"
            />
            <Input
              id="search-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What do you want to learn about?"
              className="pl-14 pr-32 h-14 text-lg neon-glow-hover bg-input/50 border-primary/30"
            />
            <Button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary hover:bg-primary/90 neon-glow"
            >
              <Sparkle size={18} className="mr-2" weight="fill" />
              Search
            </Button>
          </div>
        </form>

        {recentSearches && recentSearches.length > 0 && !hasSearched && (
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-muted-foreground">Recent:</span>
            {recentSearches.map((search, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuery(search)
                  handleSearch(search)
                }}
                className="text-sm px-3 py-1 rounded-full bg-muted/50 hover:bg-primary/20 text-foreground border border-primary/20 hover:border-primary/40 transition-all"
              >
                {search}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Filter Controls */}
      <div className="flex items-center gap-4">
        <SearchFilters
          filters={filters}
          onFiltersChange={setFilters}
          onClearFilters={handleClearFilters}
          isOpen={filtersOpen}
          onToggle={() => setFiltersOpen(!filtersOpen)}
        />
        {results.length > 0 && !isLoading && (
          <span className="text-sm text-muted-foreground">
            {results.length} {results.length === 1 ? 'result' : 'results'}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 glass-panel" />
          ))}
        </div>
      )}

      {!isLoading && hasSearched && results.length === 0 && (
        <EmptyState message="No results found. Try adjusting your filters or rephrasing your query." />
      )}

      {!isLoading && results.length > 0 && (
        <div className="space-y-4">
          {results.map((result, index) => (
            <SearchResultCard key={index} result={result} searchQuery={query} />
          ))}
        </div>
      )}

      {!hasSearched && (
        <div className="glass-panel p-12 text-center">
          <Sparkle size={64} className="mx-auto text-primary mb-4" weight="duotone" />
          <h3 className="text-xl font-semibold mb-2">Start Your Search</h3>
          <p className="text-muted-foreground">
            Enter any topic, question, or concept to find relevant insights from trusted creators.
          </p>
        </div>
      )}
    </div>
  )
}
