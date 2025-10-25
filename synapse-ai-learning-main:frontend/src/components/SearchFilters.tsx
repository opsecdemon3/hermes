import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { 
  Funnel, 
  X, 
  User, 
  Tag, 
  FolderOpen, 
  SlidersHorizontal,
  CalendarBlank,
  SortAscending
} from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { SearchFilters as FilterType, FilterOptions } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SearchFiltersProps {
  filters: FilterType
  onFiltersChange: (filters: FilterType) => void
  onClearFilters: () => void
  isOpen: boolean
  onToggle: () => void
}

export function SearchFilters({ 
  filters, 
  onFiltersChange, 
  onClearFilters,
  isOpen,
  onToggle 
}: SearchFiltersProps) {
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadFilterOptions()
  }, [])

  const loadFilterOptions = async () => {
    try {
      const data = await api.getFilterOptions()
      setOptions(data)
    } catch (error) {
      console.error('Failed to load filter options:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleCreator = (username: string) => {
    const current = filters.usernames || []
    const updated = current.includes(username)
      ? current.filter(u => u !== username)
      : [...current, username]
    onFiltersChange({ ...filters, usernames: updated.length > 0 ? updated : undefined })
  }

  const toggleExcludeCreator = (username: string) => {
    const current = filters.exclude_usernames || []
    const updated = current.includes(username)
      ? current.filter(u => u !== username)
      : [...current, username]
    onFiltersChange({ ...filters, exclude_usernames: updated.length > 0 ? updated : undefined })
  }

  const toggleTag = (tag: string) => {
    const current = filters.tags || []
    const updated = current.includes(tag)
      ? current.filter(t => t !== tag)
      : [...current, tag]
    onFiltersChange({ ...filters, tags: updated.length > 0 ? updated : undefined })
  }

  const setCategory = (category: string | undefined) => {
    onFiltersChange({ ...filters, category })
  }

  const setMinScore = (value: number[]) => {
    onFiltersChange({ ...filters, min_score: value[0] })
  }

  const activeFilterCount = [
    filters.usernames?.length || 0,
    filters.exclude_usernames?.length || 0,
    filters.tags?.length || 0,
    filters.category ? 1 : 0,
    filters.min_score && filters.min_score !== 0.15 ? 1 : 0,
  ].reduce((a, b) => a + b, 0)

  if (isLoading) {
    return null
  }

  return (
    <>
      {/* Toggle Button */}
      <Button
        onClick={onToggle}
        variant="outline"
        className="border-primary/40 text-primary hover:bg-primary/10 neon-glow-hover relative"
      >
        <Funnel size={18} className="mr-2" />
        Filters
        {activeFilterCount > 0 && (
          <Badge 
            className="ml-2 bg-hot-pink text-white border-0 px-1.5 py-0 text-xs min-w-[20px] h-5"
          >
            {activeFilterCount}
          </Badge>
        )}
      </Button>

      {/* Filter Panel */}
      {isOpen && (
        <Card className="glass-panel p-6 space-y-6 border-primary/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={24} className="text-primary" />
              <h3 className="text-lg font-semibold text-foreground">Search Filters</h3>
            </div>
            <div className="flex items-center gap-2">
              {activeFilterCount > 0 && (
                <Button
                  onClick={onClearFilters}
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X size={16} className="mr-1" />
                  Clear All
                </Button>
              )}
              <Button
                onClick={onToggle}
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground"
              >
                <X size={20} />
              </Button>
            </div>
          </div>

          {/* Creator Filters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <User size={18} className="text-cyan" />
              <h4 className="font-semibold text-sm text-foreground">Creators (WHO)</h4>
            </div>
            
            <div>
              <p className="text-xs text-muted-foreground mb-2">Include only:</p>
              <div className="flex flex-wrap gap-2">
                {options?.creators.map(creator => (
                  <Badge
                    key={creator}
                    onClick={() => toggleCreator(creator)}
                    className={cn(
                      "cursor-pointer transition-all",
                      filters.usernames?.includes(creator)
                        ? "bg-cyan/20 text-cyan border-cyan/40 hover:bg-cyan/30"
                        : "bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70"
                    )}
                  >
                    @{creator}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs text-muted-foreground mb-2">Exclude:</p>
              <div className="flex flex-wrap gap-2">
                {options?.creators.map(creator => (
                  <Badge
                    key={creator}
                    onClick={() => toggleExcludeCreator(creator)}
                    className={cn(
                      "cursor-pointer transition-all",
                      filters.exclude_usernames?.includes(creator)
                        ? "bg-red-500/20 text-red-400 border-red-500/40 hover:bg-red-500/30"
                        : "bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70"
                    )}
                  >
                    @{creator}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Category Filter */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <FolderOpen size={18} className="text-hot-pink" />
              <h4 className="font-semibold text-sm text-foreground">Category</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge
                onClick={() => setCategory(undefined)}
                className={cn(
                  "cursor-pointer transition-all",
                  !filters.category
                    ? "bg-primary/20 text-primary border-primary/40"
                    : "bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70"
                )}
              >
                All Categories
              </Badge>
              {options?.categories.map(category => (
                <Badge
                  key={category}
                  onClick={() => setCategory(category)}
                  className={cn(
                    "cursor-pointer transition-all",
                    filters.category === category
                      ? "bg-hot-pink/20 text-hot-pink border-hot-pink/40"
                      : "bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70"
                  )}
                >
                  {category}
                </Badge>
              ))}
            </div>
          </div>

          {/* Tag Filters */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Tag size={18} className="text-electric-purple" />
              <h4 className="font-semibold text-sm text-foreground">Topics (WHAT)</h4>
            </div>
            <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
              {options?.tags.slice(0, 50).map(tag => (
                <Badge
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={cn(
                    "cursor-pointer transition-all text-xs",
                    filters.tags?.includes(tag)
                      ? "bg-electric-purple/20 text-electric-purple border-electric-purple/40"
                      : "bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70"
                  )}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          {/* Relevance Score */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <SortAscending size={18} className="text-primary" />
                <h4 className="font-semibold text-sm text-foreground">Min Relevance Score</h4>
              </div>
              <span className="text-sm font-mono text-primary">
                {(filters.min_score || 0.15).toFixed(2)}
              </span>
            </div>
            <Slider
              value={[filters.min_score || 0.15]}
              onValueChange={setMinScore}
              min={0.1}
              max={0.9}
              step={0.05}
              className="py-4"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0.10 (more results)</span>
              <span>0.90 (high precision)</span>
            </div>
          </div>

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className="pt-4 border-t border-primary/20">
              <p className="text-xs text-muted-foreground mb-2">Active filters:</p>
              <div className="flex flex-wrap gap-2">
                {filters.usernames?.map(username => (
                  <Badge key={username} variant="secondary" className="text-xs">
                    Include: @{username}
                  </Badge>
                ))}
                {filters.exclude_usernames?.map(username => (
                  <Badge key={username} variant="secondary" className="text-xs">
                    Exclude: @{username}
                  </Badge>
                ))}
                {filters.category && (
                  <Badge variant="secondary" className="text-xs">
                    Category: {filters.category}
                  </Badge>
                )}
                {filters.tags?.map(tag => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    Tag: {tag}
                  </Badge>
                ))}
                {filters.min_score && filters.min_score !== 0.15 && (
                  <Badge variant="secondary" className="text-xs">
                    Min score: {filters.min_score.toFixed(2)}
                  </Badge>
                )}
              </div>
            </div>
          )}
        </Card>
      )}
    </>
  )
}
