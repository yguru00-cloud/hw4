import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { ComparedProduct } from '../types'
import StockBadge from './StockBadge'

/**
 * Products side by side: price, type, colors, sizes, availability and features. It is
 * interactive: hovering a cell highlights that product's whole column and that row, so the
 * eye can follow one product down the table.
 */
export default function ComparisonTable({ products }: { products: ComparedProduct[] }) {
  const [hovered, setHovered] = useState<number | null>(null)
  const lowestPrice = Math.min(...products.map((p) => p.price))
  const pricesDiffer = products.some((p) => p.price !== lowestPrice)

  // Props that mark a cell as part of column `i` and let it light the column up.
  const cell = (i: number, extra?: string) => ({
    className: [hovered === i ? 'col-hover' : '', extra ?? ''].filter(Boolean).join(' ') || undefined,
    onMouseEnter: () => setHovered(i),
  })

  return (
    <div className="compare" role="region" aria-label="Product comparison" onMouseLeave={() => setHovered(null)}>
      <table>
        <thead>
          <tr>
            <td />
            {products.map((p, i) => (
              <th key={p.product_id} scope="col" {...cell(i)}>
                <Link to={`/products/${p.product_id}`} className="compare-head">
                  <img src={p.image_url} alt={p.name} />
                  <span>{p.name}</span>
                </Link>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Price</th>
            {products.map((p, i) => {
              const best = pricesDiffer && p.price === lowestPrice
              return (
                <td key={p.product_id} {...cell(i, best ? 'best' : undefined)}>
                  <strong className="compare-price">${p.price.toFixed(2)}</strong>
                  {best && <small>Lowest</small>}
                </td>
              )
            })}
          </tr>
          <tr>
            <th scope="row">Type</th>
            {products.map((p, i) => (
              <td key={p.product_id} {...cell(i)}>
                {p.garment_type}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Colors</th>
            {products.map((p, i) => (
              <td key={p.product_id} {...cell(i)}>
                {p.colors.join(', ')}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Availability</th>
            {products.map((p, i) => (
              <td key={p.product_id} {...cell(i)}>
                <StockBadge
                  status={p.stock_status}
                  units={p.total_stock}
                  size={p.size}
                  sizeUnits={p.size_stock}
                />
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Sizes in stock</th>
            {products.map((p, i) => (
              <td key={p.product_id} {...cell(i)}>
                {p.sizes_in_stock.length > 0 ? p.sizes_in_stock.join(', ') : 'None'}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Features</th>
            {products.map((p, i) => (
              <td key={p.product_id} {...cell(i, 'features')}>
                {p.details}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  )
}
