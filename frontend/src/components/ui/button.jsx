import * as React from "react"
import { cn } from "@/lib/utils"

const Button = React.forwardRef(({ className, variant = "default", size = "default", ...props }, ref) => {
  const baseStyles = "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-[#0c0c0c] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#10b981] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
  
  const variants = {
    default: "bg-gradient-to-r from-[#10b981] to-[#059669] text-[#002113] hover:opacity-90 shadow-[0_0_15px_rgba(16,185,129,0.3)]",
    secondary: "bg-[#201f1f] text-[#e5e2e1] hover:bg-[#2a2a2a] border border-[#353534]",
    outline: "border border-[#3c4a42] bg-transparent hover:bg-[#201f1f] text-[#4edea3]",
    ghost: "hover:bg-[#1f1f1f] hover:text-[#e5e2e1] text-[#a1a1aa]",
    danger: "bg-[#93000a] text-[#ffdad6] hover:bg-[#690005]",
  }

  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-11 rounded-md px-8 text-base",
    icon: "h-10 w-10",
  }

  return (
    <button
      ref={ref}
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
