import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../api'
import StockBadge from '../components/StockBadge'
import type { Product } from '../types'

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) => setError(e.message))
  }, [productId])

  if (error) return <p className="status error">Could not load product: {error}</p>
  if (!product) return <p className="status">Loading…</p>

  return (
    <>
      <Link to="/products" className="back">
        ← Back to products
      </Link>
      <div className="detail">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
          {product.stock_status === 'low_stock' && (
            <span className="selling-fast">Selling Fast!</span>
          )}
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <div className="price-row">
            <p className="price price-tag large">${product.price.toFixed(2)}</p>
            <StockBadge status={product.stock_status} units={product.total_stock} />
          </div>
          <p>{product.description}</p>

          <h2>Colors</h2>
          <ul className="chips">
            {product.colors.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>

          <h2>Sizes &amp; stock</h2>
          <ul className="sizes">
            {product.inventory.map(({ size, quantity }) => (
              <li key={size} className={quantity === 0 ? 'out' : undefined}>
                <strong>{size}</strong>
                <span>{quantity === 0 ? 'Sold out' : `${quantity} in stock`}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  )
}
