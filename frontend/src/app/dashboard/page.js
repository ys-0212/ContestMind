"use client"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid } from 'recharts'
import { useRouter } from 'next/navigation'
import { useProfile, useAnalytics, useHistory, useRecommendations, useSubmissions } from "@/hooks/useAPI"
import { Loader2, BrainCircuit, Target, TrendingUp, AlertTriangle } from "lucide-react"
import { motion } from "framer-motion"

export default function DashboardPage() {
  const router = useRouter()
  const [handle, setHandle] = useState(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedHandle = localStorage.getItem('cf_handle')
      if (!storedHandle) router.push('/login')
      else setHandle(storedHandle)
    }
  }, [router])

  const { profile, isLoading: isProfileLoading } = useProfile(handle)
  const { analytics, isLoading: isAnalyticsLoading } = useAnalytics(handle)
  const { history, isLoading: isHistoryLoading } = useHistory(handle)
  const { recommendations, isLoading: isRecsLoading } = useRecommendations(handle, 5)
  const { submissions, isLoading: isSubsLoading } = useSubmissions(handle, 6)

  const loading = !handle || isProfileLoading || isAnalyticsLoading || isHistoryLoading

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center text-[#10b981]">
          <Loader2 className="h-10 w-10 animate-spin mb-4" />
          <p className="font-semibold text-sm tracking-wider uppercase">Loading Coaching Engine...</p>
        </div>
      </div>
    )
  }

  // Fallback map for rating
  const ratingData = history?.rating_changes?.map(c => ({
    name: new Date(c.ratingUpdateTimeSeconds * 1000).toLocaleString('default', { month: 'short' }),
    rating: c.newRating
  })) || []

  // Safe variables
  const totalSolved = profile?.recent_attempts_summary?.OK || 0
  const comfortZone = analytics?.rating_comfort_zone || "N/A"
  
  const difficultyData = analytics?.difficulty_distribution || []
  
  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <h1 className="text-2xl font-bold tracking-tight text-[#e5e2e1]">Analytics & Coaching</h1>
        <p className="text-sm text-[#a1a1aa] mt-1">Deep analysis of your competitive programming performance.</p>
      </motion.div>

      <motion.div 
        initial="hidden" animate="visible" 
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
        className="grid gap-6 md:grid-cols-2 lg:grid-cols-4"
      >
        {[
          { title: "Current Rating", val: profile?.current_rating || 0, sub: `Max: ${profile?.max_rating || 0}` },
          { title: "Recent Solves", val: totalSolved, sub: "Based on local attempts" },
          { title: "Comfort Zone", val: comfortZone, sub: "Ideal practice range" },
          { title: "AI Ready Status", val: "Optimal", sub: "Sufficient data for coaching", green: true }
        ].map((card, i) => (
          <motion.div key={i} variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } } }}>
            <Card className={card.green ? "bg-linear-surface border-[#10b981]/20 group hover:border-[#10b981]/50 transition-colors" : "group hover:border-[#3c4a42] transition-colors"}>
              <CardHeader className="pb-2">
                <CardTitle className={`text-sm font-medium ${card.green ? 'text-[#10b981]' : 'text-[#a1a1aa]'}`}>{card.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-[#e5e2e1] group-hover:text-[#10b981] transition-colors">{card.val}</div>
                <p className={`text-xs mt-1 ${card.green ? 'text-[#a1a1aa]' : 'text-[#10b981]'}`}>{card.sub}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Coaching Insights */}
        <Card className="md:col-span-3 border-[#4cd7f6]/20 bg-linear-surface">
          <CardHeader className="pb-3 border-b border-[#1f1f1f]">
            <CardTitle className="text-lg flex items-center text-[#4cd7f6]">
              <BrainCircuit className="mr-2 h-5 w-5" />
              ContestMind AI Coaching Insights
            </CardTitle>
            <CardDescription className="text-[#a1a1aa]">Holistic analysis of your domain knowledge and competitive strategy</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-4">
              {analytics?.holistic_weakness_insights?.map((insight) => (
                <div key={insight.substring(0, 30)} className="flex items-start">
                  <div className="mt-1 h-2 w-2 rounded-full bg-[#4cd7f6] mr-3 shrink-0"></div>
                  <p className="text-[#e5e2e1] text-sm leading-relaxed">{insight}</p>
                </div>
              ))}
              {(!analytics?.holistic_weakness_insights || analytics.holistic_weakness_insights.length === 0) && (
                <div className="text-[#a1a1aa] text-sm">No advanced insights available yet. Keep practicing!</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        <Card className="md:col-span-4">
          <CardHeader>
            <CardTitle>Rating Trajectory</CardTitle>
            <CardDescription>{analytics?.contest_participation_summary || "Your Codeforces rating trajectory"}</CardDescription>
          </CardHeader>
          <CardContent>
            {ratingData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={ratingData}>
                  <defs>
                    <linearGradient id="colorRating" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} domain={['dataMin - 100', 'dataMax + 100']} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#141414', borderColor: '#1f1f1f', color: '#e5e2e1', borderRadius: '8px' }}
                    itemStyle={{ color: '#10b981' }}
                  />
                  <Area type="monotone" dataKey="rating" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRating)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-[#a1a1aa] border border-dashed border-[#3c4a42] rounded-lg">
                No rating history available.
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle>Reasoning-Based Weakness Analysis</CardTitle>
            <CardDescription>Deep insights into why you struggle based on recent patterns</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
               <h4 className="text-xs font-semibold text-[#ef4444] uppercase tracking-wider mb-3 flex items-center">
                 <AlertTriangle className="h-3 w-3 mr-1" />
                 Tag Performance Gaps
               </h4>
              {analytics?.weakest_tags && analytics.weakest_tags.length > 0 ? (
                analytics.weakest_tags.map((w) => (
                  <div key={w} className="flex items-center justify-between border-b border-[#1f1f1f] pb-3 mb-3 last:border-0 last:pb-0">
                    <div className="flex flex-col">
                      <p className="text-sm font-medium capitalize">{w}</p>
                      <p className="text-[11px] text-[#a1a1aa] mt-0.5">High failure rate at your target rating</p>
                    </div>
                    <Badge variant="expert">Priority</Badge>
                  </div>
                ))
              ) : (
                <div className="text-sm text-[#a1a1aa]">No distinct tag weaknesses identified yet.</div>
              )}
            </div>
            
            {analytics?.holistic_weakness_insights && analytics.holistic_weakness_insights.length > 0 && (
              <div className="pt-2 border-t border-[#1f1f1f] mt-4">
                <h4 className="text-xs font-semibold text-[#f59e0b] uppercase tracking-wider mb-3 mt-4 flex items-center">
                  <BrainCircuit className="h-3 w-3 mr-1" />
                  Cognitive Blockers
                </h4>
                <div className="space-y-3">
                  {analytics.holistic_weakness_insights.slice(0, 2).map((insight) => (
                    <div key={insight.substring(0, 30)} className="text-sm text-[#e5e2e1] bg-[#1a1a1a] p-3 rounded-lg border border-[#3c4a42]">
                      "{insight}"
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-1">
        <Card>
           <CardHeader>
             <CardTitle>Difficulty Distribution</CardTitle>
             <CardDescription>Problems solved by rating bucket</CardDescription>
           </CardHeader>
           <CardContent>
             {difficultyData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={difficultyData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f1f1f" />
                    <XAxis dataKey="rating_range" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      cursor={{ fill: '#141414' }}
                      contentStyle={{ backgroundColor: '#141414', borderColor: '#1f1f1f', color: '#e5e2e1', borderRadius: '8px' }}
                    />
                    <Bar dataKey="solved_count" fill="#4cd7f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
             ) : (
                <div className="flex h-[250px] items-center justify-center text-[#a1a1aa]">No difficulty data available.</div>
             )}
           </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
           <CardHeader>
             <CardTitle className="text-[#10b981] flex items-center">
               <Target className="h-5 w-5 mr-2" />
               Recommended Problems
             </CardTitle>
             <CardDescription>Personalized based on your weaknesses and rating</CardDescription>
           </CardHeader>
           <CardContent>
             {isRecsLoading ? (
               <div className="flex justify-center py-6 text-[#10b981]"><Loader2 className="h-6 w-6 animate-spin" /></div>
             ) : recommendations?.length > 0 ? (
               <div className="space-y-4">
                 {recommendations.slice(0, 5).map(rec => (
                   <div key={rec.problem_id} onClick={() => router.push(`/dashboard/problem/${rec.problem_id}`)} className="p-3 border border-[#3c4a42] rounded-lg hover:border-[#10b981] cursor-pointer bg-[#141414] group transition-colors">
                     <div className="flex justify-between items-start mb-1">
                       <span className="font-semibold text-sm text-[#e5e2e1] group-hover:text-[#10b981]">{rec.title} ({rec.problem_id})</span>
                       <Badge variant={rec.difficulty_relation === 'stretch' ? 'expert' : rec.difficulty_relation === 'easy' ? 'easy' : 'medium'} className="text-[10px] uppercase">
                         {rec.difficulty_relation}
                       </Badge>
                     </div>
                     <p className="text-xs text-[#a1a1aa] mb-2">{rec.recommendation_reason}</p>
                     <div className="flex flex-wrap gap-1">
                       {rec.tags.slice(0, 3).map(tag => <Badge key={tag} variant="secondary" className="text-[9px] px-1 py-0">{tag}</Badge>)}
                     </div>
                   </div>
                 ))}
               </div>
             ) : (
               <div className="text-sm text-[#a1a1aa] py-4">No recommendations available. Keep practicing to get personalized suggestions!</div>
             )}
           </CardContent>
        </Card>

        <Card>
           <CardHeader>
             <CardTitle className="flex items-center">
               <TrendingUp className="h-5 w-5 mr-2 text-[#4cd7f6]" />
               Recent Submissions
             </CardTitle>
             <CardDescription>Your latest Codeforces activity</CardDescription>
           </CardHeader>
           <CardContent>
             {isSubsLoading ? (
               <div className="flex justify-center py-6 text-[#4cd7f6]"><Loader2 className="h-6 w-6 animate-spin" /></div>
             ) : submissions?.length > 0 ? (
               <div className="space-y-3">
                 {submissions.map((attempt, i) => (
                   <div key={i} className="flex justify-between items-center p-2.5 bg-[#141414] border border-[#1f1f1f] rounded-lg">
                     <div className="flex flex-col">
                       <span className="text-sm font-medium text-[#e5e2e1] cursor-pointer hover:underline" onClick={() => attempt.problem_id && router.push(`/dashboard/problem/${attempt.problem_id}`)}>
                         {attempt.title}
                       </span>
                       <span className="text-xs text-[#a1a1aa]">{new Date(attempt.creation_time * 1000).toLocaleDateString()}</span>
                     </div>
                     <Badge variant={attempt.verdict === 'OK' ? 'easy' : 'expert'} className={attempt.verdict === 'OK' ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30' : 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30'}>
                       {attempt.verdict}
                     </Badge>
                   </div>
                 ))}
               </div>
             ) : (
               <div className="text-sm text-[#a1a1aa] py-4">No recent activity found.</div>
             )}
           </CardContent>
        </Card>
      </div>
    </div>
  )
}
