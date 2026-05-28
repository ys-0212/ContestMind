import * as React from "react"
import { cn } from "@/lib/utils"

function Badge({ className, variant = "default", ...props }) {
  const baseStyles = "inline-flex items-center rounded-sm border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-[#10b981] focus:ring-offset-2"

  const variants = {
    default: "border-transparent bg-[#201f1f] text-[#e5e2e1]",
    secondary: "border-transparent bg-[#1f1f1f] text-[#a1a1aa]",
    outline: "text-[#e5e2e1] border-[#3c4a42]",
    
    // Custom Semantic Difficulty Badges
    easy: "border-transparent bg-[rgba(34,197,94,0.1)] text-[#22c55e]",
    medium: "border-transparent bg-[rgba(59,130,246,0.1)] text-[#3b82f6]",
    hard: "border-transparent bg-[rgba(249,115,22,0.1)] text-[#f97316]",
    expert: "border-transparent bg-[rgba(239,68,68,0.1)] text-[#ef4444]",
  }

  return (
    <div className={cn(baseStyles, variants[variant], className)} {...props} />
  )
}

export { Badge }
