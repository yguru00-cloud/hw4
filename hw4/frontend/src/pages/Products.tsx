import { useEffect, useMemo, useState } from 'react'
import { fetchProducts } from '../api'
import Bulldog from '../components/Bulldog'
import ProductTile from '../components/ProductTile'
import type { Product } from '../types'

const slug = (name: string) => `cat-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [active, setActive] = useState<string | null>(null)

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
  }, [])

  // The server returns products grouped by section, so the sections come out in shop order.
  const sections = useMemo(() => {
    const bySection = new Map<string, Product[]>()
    for (const p of products ?? []) {
      bySection.set(p.category, [...(bySection.get(p.category) ?? []), p])
    }
    return [...bySection.entries()]
  }, [products])

  // Highlight the category chip for the section currently in view.
  useEffect(() => {
    if (sections.length === 0) return
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) setActive(entry.target.id)
        }
      },
      { rootMargin: '-30% 0px -60% 0px' },
    )
    document.querySelectorAll('section.category').forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [sections])

  function jumpTo(id: string) {
    setActive(id)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  if (error) return <p className="status error">Could not load products: {error}</p>
  if (!products) return <p className="status">Loading products…</p>

  return (
    <>
      <header className="shop-banner">
        <div className="shop-banner-text">
          <h1>Products</h1>
          <p>
            Boola Boola! {products.length} pieces of Bulldog pride, sorted by type so you can find
            your fit fast.
          </p>
        </div>
        <Bulldog className="banner-dog" />
      </header>

      <nav className="category-nav" aria-label="Product categories">
        {sections.map(([name, items]) => (
          <a
            key={name}
            href={`#${slug(name)}`}
            className={`cat-chip${active === slug(name) ? ' active' : ''}`}
            onClick={(e) => {
              e.preventDefault()
              jumpTo(slug(name))
            }}
          >
            {name} <span>{items.length}</span>
          </a>
        ))}
      </nav>

      {sections.map(([name, items]) => (
        <section key={name} id={slug(name)} className="category" aria-labelledby={`${slug(name)}-h`}>
          <div className="category-head" data-ghost={name.split(' ')[0]}>
            <h2 id={`${slug(name)}-h`}>{name}</h2>
            <span className="category-count">{items.length}</span>
          </div>
          <div className="grid">
            {items.map((p) => (
              <ProductTile
                key={p.product_id}
                productId={p.product_id}
                name={p.name}
                price={p.price}
                imageUrl={p.image_url}
                summary={p.description}
                stockStatus={p.stock_status}
                stockUnits={p.total_stock}
              />
            ))}
          </div>
        </section>
      ))}
    </>
  )
}
