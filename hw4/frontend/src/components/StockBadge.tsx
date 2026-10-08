import type { StockStatus } from '../types'

const LABELS: Record<StockStatus, string> = {
  in_stock: 'In Stock',
  low_stock: 'Low Stock',
  out_of_stock: 'Out of Stock',
}

interface Props {
  status: StockStatus
  /** Units in stock across all sizes; shown as a tooltip when no size is given. */
  units?: number
  /** The size the status is for, when the shopper asked about one. */
  size?: string | null
  /** Units in that size. */
  sizeUnits?: number | null
}

function tooltip({ status, units, size, sizeUnits }: Props): string {
  if (size && sizeUnits != null) {
    if (status === 'out_of_stock') return `Size ${size} is sold out`
    return `Size ${size}: ${sizeUnits} ${sizeUnits === 1 ? 'unit' : 'units'} in stock`
  }
  if (units === undefined) return LABELS[status]
  if (status === 'out_of_stock') return 'Every size is sold out'
  return `${units} ${units === 1 ? 'unit' : 'units'} in stock across all sizes`
}

/**
 * A color-coded availability badge (green, amber or red). The status comes from the server,
 * worked out from the real inventory: for one size when the shopper asked about a size (shown as
 * a small size chip next to the badge), otherwise for the whole product. The label says it in
 * words, so color is never the only signal.
 */
export default function StockBadge(props: Props) {
  const { status, size } = props
  return (
    <span className="stock-line">
      <span className={`stock-badge ${status}`} title={tooltip(props)}>
        {LABELS[status]}
      </span>
      {size && (
        <span className="size-chip" title={`Availability for size ${size}`}>
          {size}
        </span>
      )}
    </span>
  )
}
