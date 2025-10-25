import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, Tag, Video as VideoIcon, TreeStructure } from '@phosphor-icons/react'
import { api } from '@/lib/api'
import type { CategoryTag, UmbrellasResponse } from '@/lib/types'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

export function CreatorDetailPage() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const [tags, setTags] = useState<CategoryTag[]>([])
  const [categories, setCategories] = useState<CategoryTag[]>([])
  const [umbrellas, setUmbrellas] = useState<UmbrellasResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [umbrellasLoading, setUmbrellasLoading] = useState(false)

  useEffect(() => {
    if (username) {
      loadCreatorData()
    }
  }, [username])

  const loadCreatorData = async () => {
    if (!username) return

    setIsLoading(true)
    try {
      const [tagsData, categoriesData] = await Promise.all([
        api.getCreatorTags(username),
        api.getCreatorCategories(username),
      ])
      setTags(tagsData)
      setCategories(categoriesData)
    } catch (error) {
      toast.error('Failed to load creator details')
      console.error('Error loading creator details:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadUmbrellas = async () => {
    if (!username || umbrellas) return
    
    setUmbrellasLoading(true)
    try {
      const data = await api.getAccountUmbrellas(username)
      setUmbrellas(data)
    } catch (error) {
      console.log('Umbrellas not available for this account (may need generation)')
      // Silent fail - umbrellas might not exist yet
    } finally {
      setUmbrellasLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel neon-glow p-6 rounded-xl">
        <Button
          variant="ghost"
          onClick={() => navigate('/library')}
          className="mb-4 text-muted-foreground hover:text-primary"
        >
          <ArrowLeft size={20} className="mr-2" />
          Back to Library
        </Button>

        <h1 className="font-mono font-bold text-3xl mb-2 text-cyan">
          @{username}
        </h1>
        <p className="text-muted-foreground">
          Explore topics, categories, and content from this creator.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-64 glass-panel" />
          <Skeleton className="h-96 glass-panel" />
        </div>
      ) : (
        <Tabs defaultValue="topics" className="space-y-6">
          <TabsList className="glass-panel">
            <TabsTrigger value="topics" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
              <Tag size={18} className="mr-2" />
              Topics
            </TabsTrigger>
            <TabsTrigger value="categories" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
              <VideoIcon size={18} className="mr-2" />
              Categories
            </TabsTrigger>
            <TabsTrigger 
              value="umbrellas" 
              className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
              onClick={loadUmbrellas}
            >
              <TreeStructure size={18} className="mr-2" />
              Umbrellas
              <Badge variant="secondary" className="ml-2 bg-cyan/20 text-cyan border-cyan/40">V2</Badge>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="topics" className="space-y-4">
            <Card className="glass-panel p-6">
              <h3 className="text-lg font-semibold mb-4 text-foreground">Topic Distribution</h3>
              <div className="flex flex-wrap gap-3">
                {tags.map((tag) => (
                  <Badge
                    key={tag.tag}
                    variant="outline"
                    className="text-sm px-4 py-2 border-primary/30 hover:border-primary/60 transition-colors"
                  >
                    {tag.tag}
                    {tag.count && (
                      <span className="ml-2 font-mono text-xs text-muted-foreground">
                        ({tag.count})
                      </span>
                    )}
                  </Badge>
                ))}
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="categories" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {categories.map((category) => (
                <Card key={category.tag} className="glass-panel p-6 neon-glow-hover">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-foreground">{category.tag}</h4>
                    {category.percentage && (
                      <span className="font-mono text-primary font-bold">
                        {category.percentage.toFixed(1)}%
                      </span>
                    )}
                  </div>
                  {category.count && (
                    <p className="text-sm text-muted-foreground">
                      {category.count} {category.count === 1 ? 'video' : 'videos'}
                    </p>
                  )}
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="umbrellas" className="space-y-4">
            {umbrellasLoading ? (
              <Skeleton className="h-64 glass-panel" />
            ) : umbrellas ? (
              <>
                <Card className="glass-panel p-6 border-cyan/30">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-cyan">Semantic Umbrellas</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        AI-clustered topic groups using {umbrellas.clustering_method} algorithm
                      </p>
                    </div>
                    <Badge variant="outline" className="border-cyan/40 text-cyan">
                      {umbrellas.umbrella_count} clusters
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Total Topics:</span>
                      <span className="ml-2 font-mono font-semibold">{umbrellas.total_topics}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Canonical Topics:</span>
                      <span className="ml-2 font-mono font-semibold">{umbrellas.canonical_topics}</span>
                    </div>
                  </div>
                </Card>

                <div className="grid grid-cols-1 gap-4">
                  {umbrellas.umbrellas.slice(0, 10).map((umbrella) => (
                    <Card key={umbrella.umbrella_id} className="glass-panel p-6 neon-glow-hover">
                      <div className="space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-foreground text-lg">
                              🌂 {umbrella.label}
                            </h4>
                            <p className="text-sm text-muted-foreground mt-1">
                              {umbrella.member_count} topics • {umbrella.video_ids.length} videos
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-muted-foreground">Coherence</div>
                            <div className="text-lg font-mono font-bold text-cyan">
                              {(umbrella.avg_coherence * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex flex-wrap gap-2">
                          {umbrella.representative_topics.slice(0, 5).map((topic, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-xs border-primary/30"
                            >
                              {topic}
                            </Badge>
                          ))}
                        </div>

                        <div className="pt-2 border-t border-border/50">
                          <div className="text-xs text-muted-foreground space-y-1">
                            <div>Frequency: {umbrella.stats.min_frequency}–{umbrella.stats.max_frequency}</div>
                            <div>Avg Score: {umbrella.stats.avg_score.toFixed(3)}</div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>

                {umbrellas.umbrella_count > 10 && (
                  <p className="text-sm text-muted-foreground text-center">
                    Showing top 10 of {umbrellas.umbrella_count} umbrellas
                  </p>
                )}
              </>
            ) : (
              <Card className="glass-panel p-8 text-center">
                <TreeStructure size={48} className="mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">Umbrellas Not Generated</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Semantic umbrellas haven't been created for this account yet.
                </p>
                <p className="text-xs text-muted-foreground font-mono">
                  Run: python umbrella_builder.py build --account {username}
                </p>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
