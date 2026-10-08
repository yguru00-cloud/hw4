import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { ProductCard } from './types'

/** The latest products the chat agent found, shared between the chat widget and the page. */
export interface ChatResultsState {
  query: string
  products: ProductCard[]
}

interface ChatResultsContextValue {
  results: ChatResultsState | null
  showResults: (results: ChatResultsState) => void
  clearResults: () => void
}

const ChatResultsContext = createContext<ChatResultsContextValue | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResultsState | null>(null)
  const showResults = useCallback((next: ChatResultsState) => setResults(next), [])
  const clearResults = useCallback(() => setResults(null), [])

  const value = useMemo(
    () => ({ results, showResults, clearResults }),
    [results, showResults, clearResults],
  )
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults(): ChatResultsContextValue {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside ChatResultsProvider')
  return ctx
}
