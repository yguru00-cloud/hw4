import { Link } from 'react-router-dom'
import type { StockStatus } from '../types'
import StockBadge from './StockBadge'

interface Props {
  productId: string
  name: string
  price: number
  imageUrl: string
  summary: string
  soldOut?: boolean
  /** When given, the card shows the availability badge (instead of the plain sold-out tag). */
  stockStatus?: StockStatus
  stockUnits?: number
  /** The size the status is for, and the units in it, when the shopper asked about a size. */
  stockSize?: string | null
  stockSizeUnits?: number | null
  lazy?: boolean
}

/**
 * A product card: photo (zooms on hover), name, summary, a clear price tag, availability, and a
 * high-contrast button. The whole card is a link that opens the product's detail view. A product
 * that is running low also gets a pulsing "Selling Fast!" badge on its photo.
 */
export default function ProductTile({
  productId,
  name,
  price,
  imageUrl,
  summary,
  soldOut = false,
  stockStatus,
  stockUnits,
  stockSize,
  stockSizeUnits,
  lazy = true,
}: Props) {
  return (
    <Link to={`/products/${productId}`} className="card">
      <div className="card-image">
        <img src={imageUrl} alt={name} loading={lazy ? 'lazy' : 'eager'} />
        {stockStatus === 'low_stock' && <span className="selling-fast">Selling Fast!</span>}
      </div>
      <div className="card-body">
        <h3>{name}</h3>
        <p className="clamp">{summary}</p>
        <div className="card-foot">
          <span className="price price-tag">${price.toFixed(2)}</span>
          {stockStatus ? (
            <StockBadge
              status={stockStatus}
              units={stockUnits}
              size={stockSize}
              sizeUnits={stockSizeUnits}
            />
          ) : (
            soldOut && <span className="sold-out-tag">Sold out</span>
          )}
        </div>
        <span className="card-cta">
          View details <span aria-hidden="true">→</span>
        </span>
      </div>
    </Link>
  )
}
