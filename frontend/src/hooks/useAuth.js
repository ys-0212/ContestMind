import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase'
import { apiClient } from '@/lib/api'

export function useAuth() {
  const [user, setUser] = useState(null)
  const [handle, setHandle] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createClient()
    
    async function loadUser() {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.user) {
          setUser(session.user)
          // Try to get handle from user metadata
          let cf_handle = session.user.user_metadata?.codeforces_handle
          if (cf_handle) {
            setHandle(cf_handle)
            localStorage.setItem('cf_handle', cf_handle)
          } else {
             cf_handle = localStorage.getItem('cf_handle')
             if (cf_handle) setHandle(cf_handle)
          }
        } else {
          setUser(null)
          setHandle(null)
          localStorage.removeItem('cf_handle')
        }
      } catch (err) {
        console.error("Auth error", err)
      } finally {
        setLoading(false)
      }
    }

    loadUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser(session.user)
        const cf_handle = session.user.user_metadata?.codeforces_handle
        if (cf_handle) {
          setHandle(cf_handle)
          localStorage.setItem('cf_handle', cf_handle)
        }
      } else {
        setUser(null)
        setHandle(null)
        localStorage.removeItem('cf_handle')
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  return { user, handle, loading }
}
