import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  UploadSimple, 
  FunnelSimple, 
  Gear, 
  Stop,
  Eye,
  CheckCircle,
  XCircle,
  Warning,
  Clock,
  ArrowRight,
  MagnifyingGlass,
  ChartBar,
  Download,
  CircleNotch
} from '@phosphor-icons/react'
import { api } from '@/lib/api'
import { toast } from 'sonner'
import type { 
  IngestionJob, 
  VideoFilter, 
  IngestionSettings,
  FilterOptions,
  AccountMetadata 
} from '@/lib/types'

export default function IngestPage() {
  const navigate = useNavigate()
  
  // Input state
  const [singleUsername, setSingleUsername] = useState('')
  const [bulkUsernames, setBulkUsernames] = useState('')
  const [inputMode, setInputMode] = useState<'single' | 'bulk'>('single')
  
  // Filter state
  const [filters, setFilters] = useState<VideoFilter>({
    skip_no_speech: true,
  })
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  
  // Settings state
  const [settings, setSettings] = useState<IngestionSettings>({
    whisper_mode: 'balanced',
    skip_existing: true,
    retranscribe_low_confidence: false,
  })
  
  // Job state
  const [currentJob, setCurrentJob] = useState<IngestionJob | null>(null)
  const [isIngesting, setIsIngesting] = useState(false)
  const [isStarting, setIsStarting] = useState(false) // Loading state for start button
  const [showFilters, setShowFilters] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  
  // Metadata preview
  const [previewMetadata, setPreviewMetadata] = useState<AccountMetadata | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  
  // Polling interval ref
  const pollingRef = useRef<number | null>(null)
  
  // Progress section ref for auto-scroll
  const progressRef = useRef<HTMLDivElement | null>(null)
  
  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions()
  }, [])
  
  // Poll for job status updates
  useEffect(() => {
    if (currentJob && isIngesting) {
      pollingRef.current = window.setInterval(async () => {
        try {
          const status = await api.getIngestionStatus(currentJob.job_id)
          setCurrentJob(status)
          
          // Stop polling if job is complete/cancelled/failed
          if (['complete', 'cancelled', 'failed'].includes(status.status)) {
            setIsIngesting(false)
            if (pollingRef.current) {
              clearInterval(pollingRef.current)
              pollingRef.current = null
            }
            
            if (status.status === 'complete') {
              toast.success('Ingestion complete!')
            } else if (status.status === 'failed') {
              toast.error('Ingestion failed')
            }
          }
        } catch (error) {
          console.error('Error polling job status:', error)
        }
      }, 1000) // Poll every second
      
      return () => {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      }
    }
  }, [currentJob, isIngesting])
  
  const loadFilterOptions = async () => {
    try {
      const options = await api.getFilterOptions()
      setFilterOptions(options)
    } catch (error) {
      console.error('Error loading filter options:', error)
    }
  }
  
  const getUsernames = (): string[] => {
    if (inputMode === 'single') {
      return singleUsername.trim() ? [singleUsername.trim()] : []
    } else {
      return bulkUsernames
        .split(/[\n,]+/)
        .map(u => u.trim())
        .filter(u => u.length > 0)
    }
  }
  
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      setBulkUsernames(text)
      setInputMode('bulk')
      toast.success('File loaded successfully')
    }
    reader.readAsText(file)
  }
  
  const handlePreviewMetadata = async () => {
    const usernames = getUsernames()
    if (usernames.length === 0) {
      toast.error('Please enter at least one username')
      return
    }
    
    setLoadingPreview(true)
    try {
      // Preview first username only
      const metadata = await api.getAccountMetadata(usernames[0])
      setPreviewMetadata(metadata)
      toast.success(`Loaded metadata for @${metadata.username}`)
    } catch (error) {
      console.error('Error loading metadata:', error)
      toast.error('Failed to load metadata. Check the username.')
    } finally {
      setLoadingPreview(false)
    }
  }
  
  const handleStartIngestion = async () => {
    const usernames = getUsernames()
    if (usernames.length === 0) {
      toast.error('Please enter at least one username')
      return
    }
    
    setIsStarting(true) // Show loading state on button
    
    try {
      // Start ingestion
      const result = await api.startIngestion({
        usernames,
        filters,
        settings,
      })
      
      toast.success(`🚀 Ingestion started for ${usernames.length} account(s)!`, {
        description: 'Scroll down to see real-time progress'
      })
      
      // Immediately show progress and start polling
      setIsIngesting(true)
      setCurrentJob({
        job_id: result.job_id,
        status: 'queued',
        overall_progress: 0,
        eta_seconds: undefined,
        elapsed_seconds: 0,
        usernames: usernames,
        accounts: usernames.map(username => ({
          username: username.replace('@', ''),
          status: 'queued',
          overall_progress: 0,
          total_videos: 0,
          filtered_videos: 0,
          processed_videos: 0,
          skipped_videos: 0,
          failed_videos: 0,
          current_video: undefined,
          videos: [],
          error: undefined
        })),
        created_at: new Date().toISOString(),
        started_at: undefined,
        completed_at: undefined,
        total_duration_seconds: 0
      })
      
      // Auto-scroll to progress section after a brief delay
      setTimeout(() => {
        progressRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
      
      // Clear inputs
      setSingleUsername('')
      setBulkUsernames('')
      setPreviewMetadata(null)
      
    } catch (error) {
      console.error('Error starting ingestion:', error)
      toast.error('Failed to start ingestion')
      setIsIngesting(false)
    } finally {
      setIsStarting(false) // Remove loading state
    }
  }
  

  
  const handleCancel = async () => {
    if (!currentJob) return
    try {
      await api.cancelIngestion(currentJob.job_id)
      setIsIngesting(false)
      setCurrentJob(null)
      toast.warning('Ingestion cancelled')
    } catch (error) {
      console.error('Error cancelling:', error)
      toast.error('Failed to cancel ingestion')
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-green-400'
      case 'failed': return 'text-red-400'
      case 'cancelled': return 'text-yellow-400'
      case 'paused': return 'text-orange-400'
      default: return 'text-primary'
    }
  }
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return <CheckCircle size={20} weight="fill" className="text-green-400" />
      case 'failed': return <XCircle size={20} weight="fill" className="text-red-400" />
      case 'cancelled': return <Warning size={20} weight="fill" className="text-yellow-400" />
      case 'queued': return <Clock size={20} weight="fill" className="text-primary" />
      default: return <ArrowRight size={20} weight="fill" className="text-primary" />
    }
  }
  
  // Format seconds to human readable time
  const formatTime = (seconds: number): string => {
    if (!seconds || seconds < 0) return '0s'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) return `${hours}h ${minutes}m`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  }
  
  // Get step display name
  const getStepName = (step?: string): string => {
    switch (step) {
      case 'fetching_metadata': return 'Fetching Metadata'
      case 'downloading': return 'Downloading'
      case 'transcribing': return 'Transcribing'
      case 'topics': return 'Extracting Topics'
      case 'embedding': return 'Generating Embeddings'
      case 'complete': return 'Complete'
      default: return step || 'Processing'
    }
  }
  
  // Get badge color for video status
  const getVideoBadgeColor = (status: string): string => {
    switch (status) {
      case 'queued': return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      case 'fetching_metadata': return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'downloading': return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
      case 'transcribing': return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'extracting_topics': return 'bg-pink-500/20 text-pink-400 border-pink-500/30'
      case 'embedding': return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'complete': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'skipped': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'failed': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-primary/20 text-primary border-primary/30'
    }
  }

  const activeFilterCount = [
    filters.last_n_videos ? 1 : 0,
    filters.history_start !== undefined || filters.history_end !== undefined ? 1 : 0,
    filters.required_category ? 1 : 0,
    filters.required_tags?.length || 0,
    filters.skip_no_speech || filters.only_with_speech ? 1 : 0
  ].reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel neon-glow p-8 rounded-xl">
        <h1 className="font-mono font-bold text-3xl mb-2 bg-gradient-to-r from-electric-purple to-hot-pink bg-clip-text text-transparent">
          INGESTION MANAGER
        </h1>
        <p className="text-muted-foreground">
          Bulk ingest TikTok accounts with advanced filtering and progress tracking
        </p>
      </div>

      {/* Input Section */}
      <Card className="glass-panel p-6">
        <div className="flex items-center gap-2 mb-4">
          <UploadSimple size={24} className="text-primary" weight="duotone" />
          <h2 className="text-xl font-semibold">Account Input</h2>
        </div>
        
        {/* Input Mode Selector */}
        <div className="flex gap-2 mb-4">
          <Button
            onClick={() => setInputMode('single')}
            variant={inputMode === 'single' ? 'default' : 'outline'}
            className={inputMode === 'single' ? 'neon-glow' : ''}
          >
            Single Username
          </Button>
          <Button
            onClick={() => setInputMode('bulk')}
            variant={inputMode === 'bulk' ? 'default' : 'outline'}
            className={inputMode === 'bulk' ? 'neon-glow' : ''}
          >
            Bulk Input
          </Button>
          <Button variant="outline" asChild>
            <label className="cursor-pointer">
              <UploadSimple size={18} className="mr-2" />
              Upload .txt
              <input
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </Button>
        </div>

        {/* Single Username Input */}
        {inputMode === 'single' && (
          <Input
            type="text"
            value={singleUsername}
            onChange={(e) => setSingleUsername(e.target.value)}
            placeholder="Enter TikTok username (e.g., @creator or creator)"
            className="bg-input/50 border-primary/30"
          />
        )}

        {/* Bulk Input */}
        {inputMode === 'bulk' && (
          <div>
            <textarea
              value={bulkUsernames}
              onChange={(e) => setBulkUsernames(e.target.value)}
              placeholder="Enter usernames (one per line or comma-separated)&#10;Example:&#10;creator1&#10;creator2, creator3"
              rows={6}
              className="w-full bg-input/50 border border-primary/30 rounded-lg px-4 py-3 text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none font-mono"
            />
            <p className="text-sm text-muted-foreground mt-2">
              {getUsernames().length} username(s) detected
            </p>
          </div>
        )}
      </Card>

      {/* Filters Section */}
      <Card className="glass-panel p-6">
        <button 
          onClick={() => setShowFilters(!showFilters)}
          className="w-full flex justify-between items-center"
        >
          <div className="flex items-center gap-2">
            <FunnelSimple size={24} className="text-primary" weight="duotone" />
            <h2 className="text-xl font-semibold">
              Video Filters
              {activeFilterCount > 0 && (
                <span className="ml-2 text-sm bg-primary text-primary-foreground px-2 py-1 rounded">
                  {activeFilterCount} active
                </span>
              )}
            </h2>
          </div>
          <span className="text-2xl">{showFilters ? '▼' : '▶'}</span>
        </button>

        {showFilters && (
          <div className="mt-6 space-y-6">
            {/* Count Filters */}
            <div>
              <label className="block text-sm text-muted-foreground mb-2 font-medium">Video Count Limit</label>
              <div className="flex flex-wrap gap-2">
                {[5, 10, 25, 50, 100].map(count => (
                  <Button
                    key={count}
                    onClick={() => setFilters({ ...filters, last_n_videos: filters.last_n_videos === count ? undefined : count })}
                    variant={filters.last_n_videos === count ? 'default' : 'outline'}
                    size="sm"
                    className={filters.last_n_videos === count ? 'neon-glow' : ''}
                  >
                    Last {count}
                  </Button>
                ))}
              </div>
            </div>

            {/* History Segment Slider */}
            <div>
              <label className="block text-sm text-muted-foreground mb-2 font-medium">
                Creator History Segment
              </label>
              <p className="text-xs text-muted-foreground mb-2">
                {filters.history_start === undefined ? 'All videos' :
                  `${Math.round((filters.history_start || 0) * 100)}% - ${Math.round((filters.history_end || 1) * 100)}% of creator's history`}
              </p>
              <div className="flex gap-4 items-center">
                <span className="text-xs text-muted-foreground">Oldest</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={(filters.history_start || 0) * 100}
                  onChange={(e) => setFilters({ ...filters, history_start: parseInt(e.target.value) / 100 })}
                  className="flex-1 accent-primary"
                />
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={(filters.history_end || 1) * 100}
                  onChange={(e) => setFilters({ ...filters, history_end: parseInt(e.target.value) / 100 })}
                  className="flex-1 accent-primary"
                />
                <span className="text-xs text-muted-foreground">Newest</span>
              </div>
            </div>

            {/* Category Filter (Macro) */}
            {filterOptions && filterOptions.categories.length > 0 && (
              <div>
                <label className="block text-sm text-muted-foreground mb-2 font-medium">
                  Account Category (Macro Filter)
                </label>
                <select
                  value={filters.required_category || ''}
                  onChange={(e) => setFilters({ ...filters, required_category: e.target.value || undefined })}
                  className="w-full bg-input/50 border border-primary/30 rounded-lg px-4 py-2 text-foreground"
                >
                  <option value="">All Categories</option>
                  {filterOptions.categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Tag Filter (Micro) */}
            {filterOptions && filterOptions.tags.length > 0 && (
              <div>
                <label className="block text-sm text-muted-foreground mb-2 font-medium">
                  Video Topics (Micro Filter)
                </label>
                <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto bg-background/30 p-3 rounded-lg border border-primary/20">
                  {filterOptions.tags.slice(0, 30).map(tag => {
                    const isSelected = filters.required_tags?.includes(tag)
                    return (
                      <button
                        key={tag}
                        onClick={() => {
                          const current = filters.required_tags || []
                          setFilters({
                            ...filters,
                            required_tags: isSelected
                              ? current.filter(t => t !== tag)
                              : [...current, tag]
                          })
                        }}
                        className={`px-3 py-1 rounded-full text-sm transition-all ${
                          isSelected
                            ? 'bg-primary text-primary-foreground neon-glow'
                            : 'bg-background/50 text-muted-foreground hover:bg-background border border-primary/20'
                        }`}
                      >
                        {tag}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Speech Detection Toggle */}
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.skip_no_speech || false}
                  onChange={(e) => setFilters({ ...filters, skip_no_speech: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
                <span className="text-sm">Skip videos with no speech</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.only_with_speech || false}
                  onChange={(e) => setFilters({ ...filters, only_with_speech: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
                <span className="text-sm">Only videos with speech</span>
              </label>
            </div>
          </div>
        )}
      </Card>

      {/* Settings Section */}
      <Card className="glass-panel p-6">
        <button 
          onClick={() => setShowSettings(!showSettings)}
          className="w-full flex justify-between items-center"
        >
          <div className="flex items-center gap-2">
            <Gear size={24} className="text-primary" weight="duotone" />
            <h2 className="text-xl font-semibold">Ingestion Settings</h2>
          </div>
          <span className="text-2xl">{showSettings ? '▼' : '▶'}</span>
        </button>

        {showSettings && (
          <div className="mt-6 space-y-6">
            {/* Whisper Mode */}
            <div>
              <label className="block text-sm text-muted-foreground mb-2 font-medium">Whisper Mode</label>
              <div className="flex gap-2">
                {(['fast', 'balanced', 'accurate', 'ultra'] as const).map(mode => (
                  <Button
                    key={mode}
                    onClick={() => setSettings({ ...settings, whisper_mode: mode })}
                    variant={settings.whisper_mode === mode ? 'default' : 'outline'}
                    size="sm"
                    className={`capitalize ${settings.whisper_mode === mode ? 'neon-glow' : ''}`}
                  >
                    {mode}
                  </Button>
                ))}
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.skip_existing || false}
                  onChange={(e) => setSettings({ ...settings, skip_existing: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
                <span className="text-sm">Skip already transcribed videos</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.retranscribe_low_confidence || false}
                  onChange={(e) => setSettings({ ...settings, retranscribe_low_confidence: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
                <span className="text-sm">Re-transcribe low confidence segments</span>
              </label>
            </div>

            {/* Max Duration */}
            <div>
              <label className="block text-sm text-muted-foreground mb-2 font-medium">
                Max Duration (minutes) - Optional
              </label>
              <Input
                type="number"
                value={settings.max_duration_minutes || ''}
                onChange={(e) => setSettings({ ...settings, max_duration_minutes: e.target.value ? parseInt(e.target.value) : undefined })}
                placeholder="No limit"
                className="bg-input/50 border-primary/30"
                min="1"
              />
            </div>
          </div>
        )}
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={handlePreviewMetadata}
          disabled={getUsernames().length === 0 || loadingPreview}
          variant="outline"
          className="flex-none"
        >
          <Eye size={18} className="mr-2" />
          {loadingPreview ? 'Loading...' : 'Preview'}
        </Button>
        <Button
          onClick={handleStartIngestion}
          disabled={getUsernames().length === 0 || isIngesting || isStarting}
          className="flex-1 neon-glow"
        >
          {isStarting ? (
            <>
              <CircleNotch size={18} className="mr-2 animate-spin" weight="bold" />
              Starting...
            </>
          ) : (
            <>
              <ArrowRight size={18} className="mr-2" weight="fill" />
              Start Ingestion ({getUsernames().length} account{getUsernames().length !== 1 ? 's' : ''})
            </>
          )}
        </Button>
      </div>

      {/* Metadata Preview */}
      {previewMetadata && (
        <Card className="glass-panel p-6 border-2 border-primary/50">
          <h3 className="text-lg font-semibold text-primary mb-3">
            Preview: @{previewMetadata.username}
          </h3>
          <p className="text-muted-foreground mb-3">
            Total Videos: {previewMetadata.total_videos}
          </p>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {previewMetadata.videos.slice(0, 10).map(video => (
              <div key={video.video_id} className="bg-background/30 rounded-lg p-3">
                <p className="text-sm font-medium text-foreground truncate">{video.title}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Views: {video.view_count.toLocaleString()} | Duration: {Math.round(video.duration)}s
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Current Job Progress */}
      {currentJob && (
        <Card 
          ref={progressRef}
          className="glass-panel p-6 border-2 border-primary/50 neon-glow relative"
        >
          {/* Live Indicator */}
          {isIngesting && currentJob.status !== 'paused' && currentJob.status !== 'complete' && (
            <div className="absolute top-4 right-4 flex items-center gap-2 bg-red-500/20 border border-red-500 rounded-full px-3 py-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-xs font-bold text-red-500 uppercase">LIVE</span>
            </div>
          )}
          
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              {getStatusIcon(currentJob.status)}
              <h3 className="text-xl font-semibold">
                {isIngesting && currentJob.status !== 'complete' ? 'Live Ingestion Progress' : 'Ingestion Job'}
              </h3>
            </div>
            <div className="flex gap-2">
              {isIngesting && (
                <Button onClick={handleCancel} variant="outline" size="sm">
                  <Stop size={16} className="mr-2" />
                  Cancel
                </Button>
              )}
            </div>
          </div>
          
          {/* Overall Progress Bar */}
          {(currentJob.overall_progress !== undefined && currentJob.overall_progress >= 0) && currentJob.status !== 'complete' && (
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">Overall Progress</span>
                  <span className="text-2xl font-bold text-primary">{Math.round(currentJob.overall_progress)}%</span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  {currentJob.elapsed_seconds > 0 && (
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Clock size={14} />
                      <span>Elapsed: <span className="text-primary font-medium">{formatTime(currentJob.elapsed_seconds)}</span></span>
                    </div>
                  )}
                  {currentJob.eta_seconds && currentJob.eta_seconds > 0 && (
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <ArrowRight size={14} />
                      <span>ETA: <span className="text-hot-pink font-medium">{formatTime(currentJob.eta_seconds)}</span></span>
                    </div>
                  )}
                </div>
              </div>
              <div className="w-full bg-background/50 rounded-full h-3 overflow-hidden border border-primary/20">
                <div 
                  className="h-full bg-gradient-to-r from-electric-purple via-hot-pink to-electric-purple bg-[length:200%_100%] animate-[shimmer_2s_ease-in-out_infinite] transition-all duration-500 ease-out"
                  style={{ width: `${Math.round(currentJob.overall_progress)}%` }}
                />
              </div>
            </div>
          )}

          <div className="space-y-4">
            {currentJob.accounts.map((account, idx) => {
              // Calculate progress percentage
              const progressPercent = account.filtered_videos > 0 
                ? Math.round((account.processed_videos / account.filtered_videos) * 100)
                : 0
              
              return (
                <div key={idx} className="bg-background/30 rounded-lg p-4 border border-primary/20">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold">@{account.username}</h4>
                    <span className={`text-sm ${getStatusColor(account.status)}`}>
                      {account.status}
                    </span>
                  </div>
                  
                  {/* Progress Bar */}
                  {account.filtered_videos > 0 && account.status !== 'failed' && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>Progress</span>
                        <span className="font-medium text-primary">{progressPercent}%</span>
                      </div>
                      <div className="w-full bg-background/50 rounded-full h-2 overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-electric-purple to-hot-pink transition-all duration-500 ease-out"
                          style={{ width: `${progressPercent}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm mb-3">
                    <div className="bg-background/50 rounded p-2">
                      <p className="text-muted-foreground text-xs">Total</p>
                      <p className="text-foreground font-medium">{account.total_videos}</p>
                    </div>
                    <div className="bg-background/50 rounded p-2">
                      <p className="text-muted-foreground text-xs">Filtered</p>
                      <p className="text-primary font-medium">{account.filtered_videos}</p>
                    </div>
                    <div className="bg-background/50 rounded p-2">
                      <p className="text-muted-foreground text-xs">Processed</p>
                      <p className="text-green-400 font-medium">{account.processed_videos}</p>
                    </div>
                    <div className="bg-background/50 rounded p-2">
                      <p className="text-muted-foreground text-xs">Skipped</p>
                      <p className="text-yellow-400 font-medium">{account.skipped_videos}</p>
                    </div>
                    <div className="bg-background/50 rounded p-2">
                      <p className="text-muted-foreground text-xs">Failed</p>
                      <p className="text-red-400 font-medium">{account.failed_videos}</p>
                    </div>
                  </div>

                  {/* Current Video / Step */}
                  {account.current_video && (
                    <div className="bg-primary/10 border border-primary/30 rounded p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Current Step:</p>
                          <p className="text-sm font-medium text-primary">
                            {getStepName(account.current_video.step)}
                          </p>
                        </div>
                        {account.current_video.progress > 0 && (
                          <div className="text-right">
                            <p className="text-xs text-muted-foreground">Progress</p>
                            <p className="text-sm font-bold text-hot-pink">{Math.round(account.current_video.progress)}%</p>
                          </div>
                        )}
                      </div>
                      <p className="text-xs text-foreground truncate">{account.current_video.title}</p>
                      <div className="mt-2">
                        <div className="w-full bg-background/30 rounded-full h-1 overflow-hidden">
                          <div 
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${Math.round(account.current_video.progress)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Video List */}
                  {account.videos && account.videos.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-muted-foreground mb-2">Videos ({account.videos.length}):</p>
                      <div className="grid grid-cols-1 gap-1 max-h-48 overflow-y-auto bg-background/20 rounded p-2">
                        {account.videos.map((video, vidIdx) => (
                          <div 
                            key={vidIdx}
                            className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-background/30"
                          >
                            <span className="truncate flex-1 text-foreground">{video.title || video.video_id}</span>
                            <span className={`ml-2 px-2 py-0.5 rounded-full text-[10px] font-medium border ${getVideoBadgeColor(video.status)}`}>
                              {getStepName(video.step)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {account.error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded p-3 mt-2">
                      <p className="text-sm text-red-400">{account.error}</p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Post-Ingestion Actions */}
          {currentJob.status === 'complete' && (
            <div className="mt-6 pt-6 border-t border-primary/20 flex flex-wrap gap-3">
              <Button
                onClick={() => navigate('/search')}
                className="neon-glow"
              >
                <MagnifyingGlass size={18} className="mr-2" weight="bold" />
                Search Semantically
              </Button>
              <Button
                onClick={() => navigate('/library')}
                variant="outline"
              >
                <ChartBar size={18} className="mr-2" />
                View Topics
              </Button>
              <Button
                onClick={() => {
                  const data = JSON.stringify(currentJob, null, 2)
                  const blob = new Blob([data], { type: 'application/json' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `ingestion_${currentJob.job_id}.json`
                  a.click()
                  toast.success('Export downloaded')
                }}
                variant="outline"
              >
                <Download size={18} className="mr-2" />
                Export Results
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
