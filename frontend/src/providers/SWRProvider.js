"use client"

import { SWRConfig } from 'swr'

export function SWRProvider({ children }) {
  return (
    <SWRConfig 
      value={{
        revalidateOnFocus: false,
        revalidateIfStale: false,
        revalidateOnReconnect: false,
        keepPreviousData: true,
      }}
    >
      {children}
    </SWRConfig>
  )
}
