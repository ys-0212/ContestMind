import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-md border border-[#3c4a42] bg-[#141414] px-3 py-2 text-sm text-[#e5e2e1] font-mono ring-offset-[#0c0c0c] file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-[#a1a1aa] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#10b981] disabled:cursor-not-allowed disabled:opacity-50 transition-all",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Input.displayName = "Input"

export { Input }
