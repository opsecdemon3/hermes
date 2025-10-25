import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  MagnifyingGlass,
  FunnelSimple,
  CaretDown,
  Clock,
  Tag,
  Video,
  ArrowRight,
  SortAscending,
  User
} from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { TranscriptItem, FilterOptions } from '@/lib/types'
import { toast } from 'sonner'

export function TranscriptsPage() {
  const navigate = useNavigate()
  
  // Data state
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([])
  const [filteredTranscripts, setFilteredTranscripts] = useState<TranscriptItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedUsername, setSelectedUsername] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedTag, setSelectedTag] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('recent')
  const [isFiltersOpen, setIsFiltersOpen] = useState(false)
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 20

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    loadTranscripts()
  }, [selectedUsername, selectedCategory, selectedTag, sortBy])

  useEffect(() => {
    // Client-side search filtering
    if (searchQuery.trim()) {
      const filtered = transcripts.filter((t) =>
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
      setFilteredTranscripts(filtered)
    } else {
      setFilteredTranscripts(transcripts)
    }
    setCurrentPage(1)
  }, [searchQuery, transcripts])

  const loadData = async () => {
    try {
      // Load filter options
      const options = await api.getFilterOptions()
      setFilterOptions(options)
    } catch (error) {
      console.error('Error loading filter options:', error)
    }
  }

  const loadTranscripts = async () => {
    setIsLoading(true)
    try {
      const username = selectedUsername !== 'all' ? selectedUsername : undefined
      const category = selectedCategory !== 'all' ? selectedCategory : undefined
      const tag = selectedTag !== 'all' ? selectedTag : undefined
      
      const data = await api.getAllTranscripts(username, category, tag, sortBy)
      setTranscripts(data.transcripts)
      setFilteredTranscripts(data.transcripts)
    } catch (error) {
      toast.error('Failed to load transcripts')
      console.error('Error loading transcripts:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  // Pagination
  const totalPages = Math.ceil(filteredTranscripts.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedTranscripts = filteredTranscripts.slice(startIndex, endIndex)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel neon-glow p-8 rounded-xl">
        <h1 className="font-mono font-bold text-3xl mb-2 bg-gradient-to-r from-neon-blue to-cyan bg-clip-text text-transparent">
          TRANSCRIPTS
        </h1>
        <p className="text-muted-foreground">
          Browse and manage all {transcripts.length} transcripts across all creators.
        </p>
        
        {/* V2 Feature Banner */}
        <div className="mt-4 p-3 rounded-lg bg-cyan/10 border border-cyan/30">
          <div className="flex items-start gap-2">
            <span className="text-cyan text-xl">⚡</span>
            <div className="flex-1">
              <p className="text-sm text-cyan font-semibold">Topic System V2 Live</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Enhanced topics with semantic umbrellas & confidence scores available via API
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="glass-panel p-6">
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <MagnifyingGlass
              size={20}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, creator, or tags..."
              className="pl-10 neon-glow-hover bg-input/50"
            />
          </div>

          {/* Filters Section */}
          <Collapsible open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
            <CollapsibleTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between border-primary/30"
              >
                <span className="flex items-center gap-2">
                  <FunnelSimple size={18} />
                  Filters
                  {(selectedUsername !== 'all' || selectedCategory !== 'all' || selectedTag !== 'all') && (
                    <Badge variant="secondary" className="ml-2">Active</Badge>
                  )}
                </span>
                <CaretDown
                  size={18}
                  className={`transition-transform ${isFiltersOpen ? 'rotate-180' : ''}`}
                />
              </Button>
            </CollapsibleTrigger>
            
            <CollapsibleContent className="mt-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Creator Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <User size={16} />
                    Creator
                  </label>
                  <Select value={selectedUsername} onValueChange={setSelectedUsername}>
                    <SelectTrigger className="bg-input/50">
                      <SelectValue placeholder="All creators" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All creators</SelectItem>
                      {filterOptions?.creators.map((creator) => (
                        <SelectItem key={creator} value={creator}>
                          @{creator}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Category Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Tag size={16} />
                    Category
                  </label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="bg-input/50">
                      <SelectValue placeholder="All categories" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All categories</SelectItem>
                      {filterOptions?.categories.map((category) => (
                        <SelectItem key={category} value={category}>
                          {category}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Tag Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Tag size={16} />
                    Topic Tag
                  </label>
                  <Select value={selectedTag} onValueChange={setSelectedTag}>
                    <SelectTrigger className="bg-input/50">
                      <SelectValue placeholder="All tags" />
                    </SelectTrigger>
                    <SelectContent className="max-h-64">
                      <SelectItem value="all">All tags</SelectItem>
                      {filterOptions?.tags.slice(0, 50).map((tag) => (
                        <SelectItem key={tag} value={tag}>
                          {tag}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Sort */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <SortAscending size={16} />
                    Sort By
                  </label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="bg-input/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="recent">Most Recent</SelectItem>
                      <SelectItem value="oldest">Oldest First</SelectItem>
                      <SelectItem value="creator">Creator (A-Z)</SelectItem>
                      <SelectItem value="duration">Longest Duration</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Clear Filters */}
              {(selectedUsername !== 'all' || selectedCategory !== 'all' || selectedTag !== 'all') && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-4 text-primary"
                  onClick={() => {
                    setSelectedUsername('all')
                    setSelectedCategory('all')
                    setSelectedTag('all')
                  }}
                >
                  Clear all filters
                </Button>
              )}
            </CollapsibleContent>
          </Collapsible>

          {/* Results Count */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {startIndex + 1}-{Math.min(endIndex, filteredTranscripts.length)} of {filteredTranscripts.length} transcripts
            </span>
          </div>
        </div>
      </Card>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-32 glass-panel" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredTranscripts.length === 0 && (
        <EmptyState message="No transcripts found. Try adjusting your filters." />
      )}

      {/* Transcripts List */}
      {!isLoading && paginatedTranscripts.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4">
            {paginatedTranscripts.map((transcript) => (
              <Card
                key={`${transcript.username}-${transcript.video_id}`}
                className="glass-panel neon-glow-hover p-6 transition-all duration-200 hover:scale-[1.01]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-3">
                    {/* Header */}
                    <div className="flex items-start gap-3">
                      <Video size={24} weight="duotone" className="text-primary shrink-0 mt-1" />
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground line-clamp-2 mb-2">
                          {transcript.title || `Video ${transcript.video_id}`}
                        </h3>
                        <div className="flex items-center gap-3 flex-wrap text-sm text-muted-foreground">
                          <span className="text-cyan font-medium">
                            @{transcript.username}
                          </span>
                          {transcript.category && (
                            <Badge variant="secondary" className="bg-secondary/20 text-secondary border-secondary/40">
                              {transcript.category}
                            </Badge>
                          )}
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {formatDuration(transcript.duration)}
                          </span>
                          <span>
                            {formatDate(transcript.processed_at)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Tags */}
                    {transcript.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {transcript.tags.slice(0, 5).map((tag, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-xs border-primary/30 text-foreground"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                      <span>{transcript.segment_count || 0} segments</span>
                      <span>{Math.round(transcript.transcription_length / 1000)}K chars</span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <Button
                    variant="outline"
                    className="border-primary/40 text-primary hover:bg-primary/10 neon-glow-hover shrink-0"
                    onClick={() => navigate(`/transcript/${transcript.username}/${transcript.video_id}`)}
                  >
                    <span className="hidden sm:inline">Open</span>
                    <ArrowRight size={18} className="sm:ml-2" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <Card className="glass-panel p-4">
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                  className="border-primary/30"
                >
                  Previous
                </Button>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </span>
                </div>
                
                <Button
                  variant="outline"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(currentPage + 1)}
                  className="border-primary/30"
                >
                  Next
                </Button>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
