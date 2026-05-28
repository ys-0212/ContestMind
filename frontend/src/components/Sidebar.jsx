"use client"
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { LayoutDashboard, List, Trophy, Settings, BrainCircuit } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const [handle, setHandle] = useState('')

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setHandle(localStorage.getItem('cf_handle') || '')
    }
  }, [])

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Problems', href: '/dashboard/problems', icon: List },
    { name: 'Contests', href: '/dashboard/contests', icon: Trophy },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  ]

  return (
    <div className="flex h-screen w-64 flex-col border-r border-[#1f1f1f] bg-[#0c0c0c] px-4 py-6 text-[#e5e2e1]">
      <div className="mb-8 flex items-center px-2">
        <BrainCircuit className="mr-3 h-6 w-6 text-[#10b981]" />
        <span className="text-xl font-bold tracking-tight">ContestMind</span>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          // Exact match for dashboard, prefix match for others so nested routes stay highlighted
          const isActive = item.href === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(item.href)
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[#1f1f1f] text-[#10b981]"
                  : "text-[#a1a1aa] hover:bg-[#141414] hover:text-[#e5e2e1]"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 flex-shrink-0",
                  isActive ? "text-[#10b981]" : "text-[#a1a1aa] group-hover:text-[#e5e2e1]"
                )}
                aria-hidden="true"
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="mt-auto px-2">
        <div 
          onClick={() => router.push('/dashboard/settings')}
          className="rounded-md bg-[#141414] border border-[#1f1f1f] p-4 text-center cursor-pointer hover:bg-[#1f1f1f] transition-colors"
        >
          <div className="flex flex-col">
            <span className="text-xs font-medium text-[#a1a1aa] uppercase tracking-wider mb-1">Codeforces Handle</span>
            <span className="font-semibold text-white tracking-wide">{handle || 'guest'}</span>
            <span className="text-xs font-medium text-[#ef4444] mt-1">{handle ? '' : 'Please log in'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
