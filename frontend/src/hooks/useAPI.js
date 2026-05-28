import useSWR from 'swr'
import { apiClient } from '@/lib/api'

export function useProfile(handle) {
  const { data, error, isLoading, mutate } = useSWR(
    handle ? `profile-${handle}` : null,
    () => apiClient.getProfile(handle),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 600_000, keepPreviousData: true }
  )
  return { profile: data, error, isLoading, mutate }
}

export function useAnalytics(handle) {
  const { data, error, isLoading, mutate } = useSWR(
    handle ? `analytics-${handle}` : null,
    () => apiClient.getAnalytics(handle),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 900_000, keepPreviousData: true }
  )
  return { analytics: data, error, isLoading, mutate }
}

export function useHistory(handle) {
  const { data, error, isLoading, mutate } = useSWR(
    handle ? `history-${handle}` : null,
    () => apiClient.getHistory(handle),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 600_000, keepPreviousData: true }
  )
  return { history: data, error, isLoading, mutate }
}

export function useSubmissions(handle, limit = 10) {
  const { data, error, isLoading, mutate } = useSWR(
    handle ? `submissions-${handle}-${limit}` : null,
    () => apiClient.getSubmissions(handle, limit),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 300_000, keepPreviousData: true }
  )
  return { submissions: data?.recent_attempts || [], error, isLoading, mutate }
}

export function useProblems(tags = "") {
  const { data, error, isLoading, mutate } = useSWR(
    `problems-${tags}`,
    () => apiClient.getProblems(tags),
    // CF problemset changes rarely — cache 24 h
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 86_400_000, keepPreviousData: true }
  )
  return { problems: data, error, isLoading, mutate }
}

export function useProblem(id) {
  const { data, error, isLoading, mutate } = useSWR(
    id ? `problem-${id}` : null,
    () => apiClient.getProblem(id),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 1_800_000, keepPreviousData: true }
  )
  return { problem: data, error, isLoading, mutate }
}

export function useSearch(query) {
  const { data, error, isLoading, mutate } = useSWR(
    query ? `search-${query}` : null,
    () => apiClient.searchProblems(query),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 300_000, keepPreviousData: true }
  )
  return { searchResults: data?.results || [], error, isLoading, mutate }
}

export function useProbability(handle, problemId) {
  const { data, error, isLoading, mutate } = useSWR(
    handle && problemId ? `probability-${handle}-${problemId}` : null,
    () => apiClient.getProbability(handle, problemId),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 900_000, keepPreviousData: true }
  )
  return { probabilityData: data, error, isLoading, mutate }
}

export function useRecommendations(handle, count = 5) {
  const { data, error, isLoading, mutate } = useSWR(
    handle ? `recommendations-${handle}-${count}` : null,
    () => apiClient.getRecommendations(handle, count),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 900_000, keepPreviousData: true }
  )
  return { recommendations: data?.recommendations || [], error, isLoading, mutate }
}

export function useAvailableProblems(minRating = 0, maxRating = 5000, limit = 500) {
  const { data, error, isLoading, mutate } = useSWR(
    `available-problems-${minRating}-${maxRating}-${limit}`,
    () => apiClient.get(`/problems/available?min_rating=${minRating}&max_rating=${maxRating}&limit=${limit}`),
    { revalidateOnFocus: false, revalidateIfStale: false, dedupingInterval: 86_400_000, keepPreviousData: true }
  )
  return { problems: data?.problems || [], count: data?.count || 0, error, isLoading, mutate }
}
