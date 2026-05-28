"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { BrainCircuit, Lock, UserPlus, ArrowRight, AlertCircle } from "lucide-react"

function validateEmail(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())
}

export default function LoginPage() {
  const router = useRouter()
  const [isLogin, setIsLogin]     = useState(true)
  const [handle,  setHandle]      = useState("")
  const [email,   setEmail]       = useState("")
  const [password, setPassword]   = useState("")
  const [error,   setError]       = useState("")
  const [isLoading, setIsLoading] = useState(false)

  // Skip login if already authenticated
  useEffect(() => {
    if (typeof window !== "undefined" && localStorage.getItem("cf_handle")) {
      router.push("/dashboard")
    }
  }, [router])

  const validate = () => {
    if (!handle.trim()) return "Codeforces handle is required."
    if (!/^[a-zA-Z0-9_.-]{2,24}$/.test(handle.trim()))
      return "Handle must be 2–24 characters (letters, digits, _ - . only)."
    if (!validateEmail(email)) return "Enter a valid email address."
    if (password.length < 8) return "Password must be at least 8 characters."
    return ""
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError("")

    const msg = validate()
    if (msg) { setError(msg); return }

    setIsLoading(true)
    // MVP: localStorage session — replace with Supabase signUp/signIn when ready
    localStorage.setItem("cf_handle", handle.trim())
    setTimeout(() => router.push("/dashboard"), 500)
  }

  const switchMode = (login) => {
    setIsLogin(login)
    setError("")
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0c0c0c] text-[#e5e2e1] px-4">
      <div className="absolute inset-0 -z-10 h-full w-full bg-[radial-gradient(#1f1f1f_1px,transparent_1px)] [background-size:24px_24px] opacity-30" />

      <div className="w-full max-w-md animate-in fade-in zoom-in-95 duration-500">
        <div className="flex flex-col items-center mb-8 cursor-pointer" onClick={() => router.push("/")}>
          <div className="relative">
            <BrainCircuit className="h-12 w-12 text-[#10b981] mb-3 relative z-10" />
            <div className="absolute inset-0 bg-[#10b981] blur-2xl opacity-20 rounded-full" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">ContestMind</h1>
          <p className="text-[#a1a1aa] text-sm mt-2 text-center">
            {isLogin ? "Welcome back. Ready to train?" : "Join the elite competitive programming platform."}
          </p>
        </div>

        <Card className="border-[#3c4a42] bg-[#141414]/90 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#10b981] to-transparent opacity-50" />

          <div className="flex w-full border-b border-[#1f1f1f]">
            <button
              className={`flex-1 py-4 text-sm font-semibold transition-colors ${isLogin ? "text-[#10b981] border-b-2 border-[#10b981] bg-[#1a1a1a]/50" : "text-[#a1a1aa] hover:text-[#e5e2e1]"}`}
              onClick={() => switchMode(true)}
            >
              Sign In
            </button>
            <button
              className={`flex-1 py-4 text-sm font-semibold transition-colors ${!isLogin ? "text-[#10b981] border-b-2 border-[#10b981] bg-[#1a1a1a]/50" : "text-[#a1a1aa] hover:text-[#e5e2e1]"}`}
              onClick={() => switchMode(false)}
            >
              Create Account
            </button>
          </div>

          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-5" noValidate>
              {/* Codeforces handle — required on both login and signup */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider">
                  Codeforces Handle
                </label>
                <Input
                  type="text"
                  placeholder="tourist"
                  value={handle}
                  onChange={e => { setHandle(e.target.value); setError("") }}
                  className="bg-[#0c0c0c] border-[#3c4a42] focus:border-[#10b981]"
                  autoComplete="username"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider">
                  Email Address
                </label>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => { setEmail(e.target.value); setError("") }}
                  className="bg-[#0c0c0c] border-[#3c4a42] focus:border-[#10b981]"
                  autoComplete="email"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider">
                  Password
                </label>
                <Input
                  type="password"
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={e => { setPassword(e.target.value); setError("") }}
                  className="bg-[#0c0c0c] border-[#3c4a42] focus:border-[#10b981]"
                  autoComplete={isLogin ? "current-password" : "new-password"}
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-sm text-[#ef4444] bg-[#ef4444]/10 border border-[#ef4444]/30 rounded px-3 py-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full h-12 text-base font-medium mt-2 group bg-[#10b981] hover:bg-[#059669] text-[#002113]"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <span className="h-4 w-4 border-2 border-[#002113] border-t-transparent rounded-full animate-spin mr-2" />
                    Authenticating…
                  </span>
                ) : (
                  <>
                    {isLogin ? <Lock className="mr-2 h-4 w-4" /> : <UserPlus className="mr-2 h-4 w-4" />}
                    {isLogin ? "Sign In to Dashboard" : "Create Account"}
                    <ArrowRight className="ml-2 h-4 w-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
                  </>
                )}
              </Button>
            </form>

            <p className="text-center text-xs text-[#52525b] mt-5">
              MVP: sessions stored locally. Real Supabase auth coming soon.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
