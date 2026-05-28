"use client"
import { Sidebar } from "./Sidebar"
import { Search, Flame, LogOut, Settings } from "lucide-react"
import { useRouter } from 'next/navigation'
import { useState, useEffect, useRef } from "react"

export function DashboardLayout({ children }) {
  const router = useRouter()
  const [handle, setHandle] = useState("")
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setHandle(localStorage.getItem('cf_handle') || '')
    }
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowUserMenu(false)
      }
    }
    if (showUserMenu) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [showUserMenu])

  const handleLogout = () => {
    localStorage.removeItem("cf_handle")
    setShowUserMenu(false)
    router.push("/login")
  }

  return (
    <div className="flex h-screen w-full bg-[#0c0c0c] text-[#e5e2e1]">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center justify-between border-b border-[#1f1f1f] bg-[#0c0c0c] px-6">
          <div className="flex items-center w-full max-w-md">
            <div className="relative w-full">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <Search className="h-4 w-4 text-[#a1a1aa]" />
              </div>
              <input
                type="text"
                className="block w-full rounded-md border border-[#3c4a42] bg-[#141414] py-1.5 pl-10 pr-3 text-sm text-[#e5e2e1] placeholder:text-[#a1a1aa] focus:border-[#10b981] focus:outline-none focus:ring-1 focus:ring-[#10b981]"
                placeholder="Search problems, contests, algorithms..."
              />
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center bg-[#1f1f1f] px-3 py-1 rounded-full border border-[#3c4a42]">
              <Flame className={`h-4 w-4 mr-2 ${handle ? 'text-[#f59e0b]' : 'text-[#a1a1aa]'}`} />
              <span className="text-sm font-bold text-[#e5e2e1]">{handle ? 'Active' : 'Offline'}</span>
            </div>

            {/* Avatar + dropdown */}
            <div className="relative" ref={menuRef}>
              <div
                onClick={() => setShowUserMenu(v => !v)}
                className="h-8 w-8 rounded-sm bg-gradient-to-br from-[#10b981] to-[#059669] flex items-center justify-center font-bold text-[#002113] cursor-pointer hover:opacity-80 transition-opacity select-none"
                title={handle || "Guest"}
              >
                {handle ? handle.charAt(0).toUpperCase() : 'G'}
              </div>

              {showUserMenu && (
                <div className="absolute right-0 top-10 w-52 bg-[#141414] border border-[#3c4a42] rounded-lg shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
                  {/* Handle info */}
                  <div className="px-4 py-3 border-b border-[#1f1f1f]">
                    <p className="text-[10px] text-[#a1a1aa] uppercase tracking-wider font-semibold">Signed in as</p>
                    <p className="text-sm font-semibold text-[#e5e2e1] truncate mt-0.5">{handle || "Guest"}</p>
                  </div>

                  {/* Settings */}
                  <button
                    onClick={() => { setShowUserMenu(false); router.push('/dashboard/settings') }}
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#a1a1aa] hover:text-[#e5e2e1] hover:bg-[#1f1f1f] transition-colors"
                  >
                    <Settings className="h-4 w-4 shrink-0" />
                    Settings
                  </button>

                  {/* Sign Out */}
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-[#ef4444] hover:bg-[#1f1f1f] transition-colors border-t border-[#1f1f1f]"
                  >
                    <LogOut className="h-4 w-4 shrink-0" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-[#0c0c0c] p-6">
          <div className="mx-auto max-w-[1440px]">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
