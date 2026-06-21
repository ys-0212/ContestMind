"use client"
import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Filter, Circle, Loader2, BookOpen, X, SlidersHorizontal } from "lucide-react"

import { useAvailableProblems, useSearch } from "@/hooks/useAPI"

const DISPLAY_LIMIT = 250

const COMMON_TAGS = [
  "implementation", "math", "greedy", "dp", "data structures",
  "brute force", "constructive algorithms", "graphs", "sortings",
  "binary search", "two pointers", "strings", "trees", "number theory",
  "dfs and similar", "shortest paths", "bitmasks", "combinatorics",
]

export default function ProblemsPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [showAll, setShowAll] = useState(false)

  // ── Filters ──────────────────────────────────────────────────────────────
  const [filterOpen, setFilterOpen] = useState(false)
  const [filterMinRating, setFilterMinRating] = useState("")
  const [filterMaxRating, setFilterMaxRating] = useState("")
  const [filterTags, setFilterTags] = useState([])

  const activeFilterCount = (filterMinRating ? 1 : 0) + (filterMaxRating ? 1 : 0)
    + filterTags.length

  const clearFilters = () => {
    setFilterMinRating("")
    setFilterMaxRating("")
    setFilterTags([])
  }

  const toggleTag = (tag) =>
    setFilterTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchTerm), 500)
    return () => clearTimeout(timer)
  }, [searchTerm])

  const { problems: baseProblems, count: totalCount, isLoading: loadingAll } = useAvailableProblems(0, 5000, 500)

  const { searchResults, isLoading: loadingSearch } = useSearch(
    debouncedSearch.length >= 3 ? debouncedSearch : null
  )

  // Dynamic POTD: prefer problems in 1300–1800 range
  const potdProblem = useMemo(() => {
    const fallback = baseProblems.filter(p => p.rating && p.rating >= 1300 && p.rating <= 1800)
    const candidates = fallback.length > 0 ? fallback : baseProblems
    if (!candidates.length) return null
    const dayIdx = Math.floor(Date.now() / 86400000)
    return candidates[dayIdx % candidates.length]
  }, [baseProblems])

  const scrapedCount = useMemo(() => baseProblems.filter(p => p.has_statement).length, [baseProblems])

  const lowerSearch = searchTerm.toLowerCase()

  // ── Apply active filters to a pool of problems ──────────────────────────
  const applyFilters = (problems) => {
    let result = problems
    if (filterMinRating) result = result.filter(p => p.rating && p.rating >= Number(filterMinRating))
    if (filterMaxRating) result = result.filter(p => p.rating && p.rating <= Number(filterMaxRating))
    if (filterTags.length > 0) {
      result = result.filter(p => filterTags.every(tag => (p.tags || []).includes(tag)))
    }
    return result
  }

  const problemsToDisplay = useMemo(() => {
    const filtered = applyFilters(baseProblems)

    // No search → show filtered pool up to DISPLAY_LIMIT
    if (!lowerSearch) {
      return filtered.slice(0, showAll ? undefined : DISPLAY_LIMIT)
    }

    const searchUpper = searchTerm.trim().toUpperCase()

    // Client-side text filter (title, ID, tags)
    let clientFiltered = filtered.filter(p =>
      (p.title  || "").toLowerCase().includes(lowerSearch) ||
      (p.problem_id || "").toLowerCase().includes(lowerSearch) ||
      (p.tags   || []).some(tag => tag.toLowerCase().includes(lowerSearch))
    )

    // Sort by match quality: exact ID first, then ID prefix, then title prefix
    clientFiltered = [...clientFiltered].sort((a, b) => {
      const score = p => {
        if (p.problem_id === searchUpper) return 3
        if (p.problem_id.startsWith(searchUpper)) return 2
        if ((p.title || "").toUpperCase().startsWith(searchUpper)) return 1
        return 0
      }
      return score(b) - score(a)
    })

    // Merge semantic results on top if available (deduped)
    if (debouncedSearch.length >= 3 && searchResults.length > 0) {
      const semanticIds = new Set(searchResults.map(r => (r.problem_id || "").toUpperCase()))
      const enrichedSemantic = searchResults
        .map(r => {
          const full = baseProblems.find(p => p.problem_id === (r.problem_id || "").toUpperCase())
          return full || { ...r, title: r.title || r.name || "", tags: r.tags || [], has_statement: false }
        })
        .filter(r => {
          // Apply active filters to semantic results too
          if (filterMinRating && r.rating && r.rating < Number(filterMinRating)) return false
          if (filterMaxRating && r.rating && r.rating > Number(filterMaxRating)) return false
          if (filterScrapedOnly && !r.has_statement) return false
          if (filterTags.length > 0 && !filterTags.every(tag => (r.tags || []).includes(tag))) return false
          return true
        })
      const remaining = clientFiltered.filter(p => !semanticIds.has(p.problem_id))
      return [...enrichedSemantic, ...remaining]
    }

    return clientFiltered
  }, [
    baseProblems, lowerSearch, debouncedSearch, searchResults, showAll,
    filterMinRating, filterMaxRating, filterScrapedOnly, filterTags, searchTerm,
  ])

  const getDiffBadge = (rating) => {
    if (!rating) return "medium"
    if (rating < 1200) return "easy"
    if (rating < 1600) return "medium"
    if (rating < 2000) return "hard"
    return "expert"
  }

  const loading = loadingAll

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* ── Problem of the Day ─────────────────────────────────────────────── */}
      {(potdProblem || !loadingAll) && (
        <Card
          className="border-[#10b981]/30 bg-gradient-to-r from-[#141414] to-[#0c0c0c] mb-8 overflow-hidden relative cursor-pointer group"
          onClick={() => potdProblem && router.push(`/dashboard/problem/${potdProblem.problem_id}`)}
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#10b981] opacity-5 blur-3xl group-hover:opacity-10 transition-opacity" />
          <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center">
              <div className="h-12 w-12 rounded-full bg-[#10b981]/10 flex items-center justify-center mr-6 border border-[#10b981]/30">
                <span className="text-xl">🔥</span>
              </div>
              <div>
                <div className="text-[#10b981] font-bold text-sm tracking-widest uppercase mb-1">Problem of the Day</div>
                {potdProblem ? (
                  <>
                    <h2 className="text-xl font-bold text-[#e5e2e1] group-hover:underline">
                      {potdProblem.title} ({potdProblem.problem_id})
                    </h2>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {(potdProblem.tags || []).slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                      ))}
                      {potdProblem.has_statement && (
                        <Badge className="text-[10px] bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30">Full Problem</Badge>
                      )}
                    </div>
                  </>
                ) : (
                  <h2 className="text-xl font-bold text-[#e5e2e1]">Loading…</h2>
                )}
              </div>
            </div>
            <div className="mt-4 md:mt-0 flex items-center space-x-2">
              {potdProblem && <Badge variant={getDiffBadge(potdProblem.rating)}>{potdProblem.rating}</Badge>}
              <Button className="bg-[#10b981] text-[#002113] hover:bg-[#059669]" disabled={!potdProblem}>
                Solve Now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Header + Search + Filter toggle ──────────────────────────────── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#e5e2e1]">Problem Set</h1>
          {!loadingAll && (
            <p className="text-sm text-[#a1a1aa] mt-1">
              <span className="text-[#10b981] font-semibold">{scrapedCount}</span> full problems ·{" "}
              <span className="text-[#e5e2e1] font-semibold">{totalCount}</span> total available
            </p>
          )}
        </div>
        <div className="flex w-full sm:w-auto items-center space-x-2">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-[#a1a1aa]" />
            <Input
              type="text"
              placeholder="Search by ID, title, or tag…"
              className="pl-9"
              value={searchTerm}
              onChange={e => { setSearchTerm(e.target.value); setShowAll(false) }}
            />
          </div>
          <Button
            variant="outline"
            className={`shrink-0 relative ${filterOpen ? "border-[#10b981] text-[#10b981]" : ""}`}
            onClick={() => setFilterOpen(v => !v)}
          >
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Filter
            {activeFilterCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 h-4 w-4 rounded-full bg-[#10b981] text-[#002113] text-[10px] font-bold flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </Button>
        </div>
      </div>

      {/* ── Filter panel ──────────────────────────────────────────────────── */}
      {filterOpen && (
        <div className="rounded-lg border border-[#3c4a42] bg-[#141414] p-4 space-y-4 animate-in slide-in-from-top-2 fade-in duration-200">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider">Active Filters</span>
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="text-[10px] text-[#a1a1aa] hover:text-[#ef4444] flex items-center gap-1 transition-colors"
              >
                <X className="h-3 w-3" /> Clear all
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div>
              <label className="text-[10px] text-[#a1a1aa] font-semibold uppercase tracking-wider block mb-1">Min Rating</label>
              <input
                type="number" min="0" max="4000" step="100"
                value={filterMinRating}
                onChange={e => setFilterMinRating(e.target.value)}
                className="w-full bg-[#0c0c0c] border border-[#3c4a42] rounded px-2.5 py-1.5 text-sm text-[#e5e2e1] focus:outline-none focus:border-[#10b981] transition-colors"
                placeholder="800"
              />
            </div>
            <div>
              <label className="text-[10px] text-[#a1a1aa] font-semibold uppercase tracking-wider block mb-1">Max Rating</label>
              <input
                type="number" min="0" max="4000" step="100"
                value={filterMaxRating}
                onChange={e => setFilterMaxRating(e.target.value)}
                className="w-full bg-[#0c0c0c] border border-[#3c4a42] rounded px-2.5 py-1.5 text-sm text-[#e5e2e1] focus:outline-none focus:border-[#10b981] transition-colors"
                placeholder="3500"
              />
            </div>
            <div className="flex items-end">
              {/* Removed Full statement only filter since problems are loaded on demand */}
            </div>
          </div>

          {/* Tag chips */}
          <div>
            <label className="text-[10px] text-[#a1a1aa] font-semibold uppercase tracking-wider block mb-2">Filter by Topic</label>
            <div className="flex flex-wrap gap-1.5">
              {COMMON_TAGS.map(tag => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`text-[11px] px-2.5 py-0.5 rounded-full border transition-colors ${
                    filterTags.includes(tag)
                      ? "bg-[#10b981]/20 border-[#10b981]/60 text-[#10b981]"
                      : "bg-[#0c0c0c] border-[#3c4a42] text-[#a1a1aa] hover:border-[#10b981]/40 hover:text-[#e5e2e1]"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Problem Table ─────────────────────────────────────────────────── */}
      <Card className="border-[#1f1f1f] bg-[#0c0c0c] overflow-hidden min-h-[400px]">
        <div className="grid grid-cols-12 gap-4 border-b border-[#1f1f1f] bg-[#141414] px-6 py-3 text-xs font-semibold uppercase tracking-wider text-[#a1a1aa]">
          <div className="col-span-1 text-center">Status</div>
          <div className="col-span-2">Problem ID</div>
          <div className="col-span-5">Title &amp; Tags</div>
          <div className="col-span-2 text-center">Difficulty</div>
          <div className="col-span-2 text-right">Action</div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center h-[300px] text-[#10b981]">
            <Loader2 className="h-8 w-8 animate-spin mb-4" />
            <span className="text-sm font-semibold tracking-widest uppercase">Fetching problems…</span>
          </div>
        ) : (
          <>
            <div className="divide-y divide-[#1f1f1f]">
              {problemsToDisplay.map(problem => (
                <div
                  key={problem.problem_id}
                  className="grid grid-cols-12 gap-4 items-center px-6 py-4 hover:bg-[#141414] transition-colors cursor-pointer"
                  onClick={() => router.push(`/dashboard/problem/${problem.problem_id}`)}
                >
                  <div className="col-span-1 flex justify-center">
                    <Circle className="h-5 w-5 text-[#3c4a42]" />
                  </div>

                  <div className="col-span-2 font-mono text-sm text-[#bbcabf] flex items-center gap-1.5">
                    {problem.problem_id}
                    {problem.has_statement && (
                      <BookOpen className="h-3 w-3 text-[#10b981] shrink-0" title="Full statement available" />
                    )}
                  </div>

                  <div className="col-span-5">
                    <div className="font-medium text-[#e5e2e1] mb-1">{problem.title}</div>
                    <div className="flex flex-wrap gap-1">
                      {(problem.tags || []).slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">{tag}</Badge>
                      ))}
                      {(problem.tags || []).length > 3 && (
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          +{problem.tags.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="col-span-2 flex justify-center">
                    <Badge variant={getDiffBadge(problem.rating)}>{problem.rating || "N/A"}</Badge>
                  </div>

                  <div className="col-span-2 flex justify-end">
                    <Button size="sm" variant="ghost" className="h-8">Solve</Button>
                  </div>
                </div>
              ))}

              {problemsToDisplay.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center h-[200px] text-[#a1a1aa] gap-2">
                  <Search className="h-8 w-8 text-[#3c4a42]" />
                  <p className="text-sm">No problems match your filters.</p>
                  {activeFilterCount > 0 && (
                    <button onClick={clearFilters} className="text-xs text-[#10b981] hover:underline">
                      Clear filters
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Show more button */}
            {!lowerSearch && !showAll && applyFilters(baseProblems).length > DISPLAY_LIMIT && (
              <div className="flex justify-center py-6 border-t border-[#1f1f1f]">
                <Button
                  variant="outline"
                  className="border-[#3c4a42] text-[#a1a1aa] hover:text-[#e5e2e1] hover:bg-[#141414]"
                  onClick={() => setShowAll(true)}
                >
                  Show all {applyFilters(baseProblems).length} problems
                </Button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
