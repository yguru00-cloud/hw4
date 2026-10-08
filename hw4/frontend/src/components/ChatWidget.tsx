import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { fetchChatHistory, sendChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import { pageContextFor } from '../pageContext'
import type { ChatTurn, ComparedProduct, ProductCard } from '../types'
import ComparisonTable from './ComparisonTable'
import StockBadge from './StockBadge'

interface Message extends ChatTurn {
  products?: ProductCard[]
  comparison?: ComparedProduct[]
}

// The server accepts at most 20 earlier turns.
const MAX_HISTORY = 20

const greeting = (firstName?: string | null): Message => ({
  role: 'assistant',
  content: `${firstName ? `Hi ${firstName}!` : 'Hi!'} Ask me about our products, sizes, or what is in stock.`,
})

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([greeting()])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const { showResults } = useChatResults()
  const endRef = useRef<HTMLDivElement>(null)

  // Logged-in customers get their saved conversation back when the widget starts and whenever
  // they log in. Guests (and logged-out visitors) start from a clean greeting; nothing of theirs
  // is stored on the server.
  const userId = user?.id
  const firstName = user?.first_name
  useEffect(() => {
    if (loading) return
    setMessages([greeting(firstName)])
    if (userId === undefined) return
    let cancelled = false
    fetchChatHistory()
      .then((saved) => {
        if (cancelled || saved.length === 0) return
        setMessages([
          greeting(firstName),
          ...saved.map(({ role, content, products, comparison }) => ({
            role,
            content,
            products,
            comparison,
          })),
        ])
      })
      .catch(() => {
        // No saved history to show; the greeting is enough.
      })
    return () => {
      cancelled = true
    }
  }, [loading, userId, firstName])

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [messages, open])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return
    // Earlier turns give a guest's agent its context (a logged-in customer's come from the
    // server); skip the local greeting at index 0.
    const history = messages
      .slice(1)
      .slice(-MAX_HISTORY)
      .map(({ role, content }) => ({ role, content }))
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setSending(true)
    try {
      // The page the shopper is on goes with the message, so "this" can mean the open product.
      const { reply, products, comparison } = await sendChatMessage(
        text,
        history,
        pageContextFor(pathname),
      )
      setMessages((m) => [...m, { role: 'assistant', content: reply, products, comparison }])
      // Matching products also go onto the page as cards; replies without any leave them alone.
      if (products.length > 0) showResults({ query: text, products })
    } catch (err) {
      const content =
        err instanceof TypeError
          ? 'Sorry, I could not reach the server. Please try again.'
          : err instanceof Error
            ? err.message
            : 'Something went wrong. Please try again.'
      setMessages((m) => [...m, { role: 'assistant', content }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat">
      {open && (
        <section
          className={`chat-panel${messages.some((m) => m.comparison?.length) ? ' wide' : ''}`}
          aria-label="Chat assistant"
        >
          <header>
            <div className="chat-title">
              <span className="chat-avatar" aria-hidden="true">
                CC
              </span>
              <div>
                <strong>Campus Customs Assistant</strong>
                <span className="online">
                  <span className="online-dot" aria-hidden="true" />
                  Online
                </span>
              </div>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.role}`}>
                <div className={`bubble ${m.role}`}>{m.content}</div>
                {m.products && m.products.length > 0 && (
                  <ul className="chat-cards">
                    {m.products.map((p) => (
                      <li key={p.product_id}>
                        <Link to={`/products/${p.product_id}`} className="chat-card">
                          <img src={p.image_url} alt={p.name} />
                          <span className="chat-card-name">{p.name}</span>
                          <span className="chat-card-meta">${p.price.toFixed(2)}</span>
                          <StockBadge
                            status={p.stock_status}
                            units={p.total_stock}
                            size={p.size}
                            sizeUnits={p.size_stock}
                          />
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
                {m.comparison && m.comparison.length >= 2 && (
                  <ComparisonTable products={m.comparison} />
                )}
              </div>
            ))}
            {sending && (
              <div className="message assistant">
                <div className="bubble assistant typing" role="status" aria-label="Assistant is typing">
                  <i />
                  <i />
                  <i />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
          <form onSubmit={onSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
              aria-label="Message"
            />
            <button type="submit" disabled={sending}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? '×' : 'Chat'}
        {!open && <span className="toggle-dot" aria-hidden="true" />}
      </button>
    </div>
  )
}
