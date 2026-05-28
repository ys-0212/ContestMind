"use client"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Trophy, Clock, Calendar, ChevronRight, Loader2 } from "lucide-react"

export default function ContestsPage() {
  const [contests, setContests] = useState([])
  const [pastContests, setPastContests] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchContests = async () => {
      try {
        const handle = localStorage.getItem('cf_handle')
        // Fetch upcoming contests
        const res = await fetch("https://codeforces.com/api/contest.list")
        const data = await res.json()
        if (data.status === "OK") {
          const upcoming = data.result.filter(c => c.phase === "BEFORE").reverse().slice(0, 1)
          setContests(upcoming)
        }
        
        // Fetch past contests (rating history)
        if (handle) {
          const pastRes = await fetch(`https://codeforces.com/api/user.rating?handle=${handle}`)
          const pastData = await pastRes.json()
          if (pastData.status === "OK") {
            setPastContests(pastData.result.reverse().slice(0, 10))
          }
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchContests()
  }, [])

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#10b981]" />
      </div>
    )
  }

  const nextContest = contests[0]

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#e5e2e1]">Contest History</h1>
        <p className="text-sm text-[#a1a1aa] mt-1">Track your rated rounds and upcoming competitions.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="col-span-1 border-[#10b981]/30 bg-linear-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <Trophy className="mr-2 h-5 w-5 text-[#10b981]" />
              Next Contest
            </CardTitle>
          </CardHeader>
          <CardContent>
            {nextContest ? (
              <>
                <div className="text-xl font-bold text-[#e5e2e1] mb-2">{nextContest.name}</div>
                <div className="flex items-center text-sm text-[#a1a1aa] mb-4">
                  <Clock className="mr-2 h-4 w-4 text-[#4cd7f6]" />
                  Starts in {Math.round(-nextContest.relativeTimeSeconds / 3600)} hours
                </div>
                <Button className="w-full bg-[#10b981] hover:bg-[#059669] text-[#002113]">Register on Codeforces</Button>
              </>
            ) : (
              <div className="text-[#a1a1aa]">No upcoming contests found.</div>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader className="pb-3 border-b border-[#1f1f1f]">
            <CardTitle className="text-lg flex items-center">
              <Calendar className="mr-2 h-5 w-5 text-[#a1a1aa]" />
              Recent Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-[#1f1f1f]">
              {pastContests.map((contest) => (
                <div key={contest.contestId} className="flex items-center justify-between p-4 hover:bg-[#141414] transition-colors cursor-pointer">
                  <div className="flex flex-col">
                    <span className="font-medium text-[#e5e2e1]">{contest.contestName}</span>
                    <span className="text-sm text-[#a1a1aa] mt-1">
                      {new Date(contest.ratingUpdateTimeSeconds * 1000).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-8">
                    <div className="text-right">
                      <div className="text-sm text-[#a1a1aa]">Rank</div>
                      <div className="font-mono text-[#e5e2e1]">{contest.rank}</div>
                    </div>
                    <div className="text-right w-16">
                      <div className="text-sm text-[#a1a1aa]">Δ</div>
                      <div className={`font-mono font-bold ${(contest.newRating - contest.oldRating) > 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                        {(contest.newRating - contest.oldRating) > 0 ? '+' : ''}{contest.newRating - contest.oldRating}
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-[#3c4a42]" />
                  </div>
                </div>
              ))}
              {pastContests.length === 0 && (
                <div className="p-8 text-center text-[#a1a1aa]">No past contests found. Make sure you entered a valid handle.</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
