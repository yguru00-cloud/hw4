import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useChatResults } from '../chatResults'
import ProductTile from './ProductTile'

// Pages where the results section would get in the way (the detail view and the forms).
const hiddenOn = (pathname: string) =>
  pathname.startsWith('/products/') || pathname === '/login' || pathname === '/register'

/** Shows the products the chat agent found as cards on the page, above the page content. */
export default function ChatResults() {
  const { results, clearResults } = useChatResults()
  const { pathname } = useLocation()
  const ref = useRef<HTMLElement>(null)

  // Bring new results into view when they arrive.
  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [results])

  if (!results || hiddenOn(pathname)) return null

  const count = results.products.length
  return (
    <section className="results" ref={ref} aria-label="Chat results">
      <div className="results-header">
        <div>
          <h2>Results from chat</h2>
          <p>
            {count} {count === 1 ? 'product' : 'products'} for “{results.query}”
          </p>
        </div>
        <button type="button" className="button button-small" onClick={clearResults}>
          Clear
        </button>
      </div>
      <div className="grid">
        {results.products.map((p) => (
          <ProductTile
            key={p.product_id}
            productId={p.product_id}
            name={p.name}
            price={p.price}
            imageUrl={p.image_url}
            summary={p.summary}
            stockStatus={p.stock_status}
            stockUnits={p.total_stock}
            stockSize={p.size}
            stockSizeUnits={p.size_stock}
            lazy={false}
          />
        ))}
      </div>
    </section>
  )
}
