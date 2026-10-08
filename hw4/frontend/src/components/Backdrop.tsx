function Paw({ className }: { className: string }) {
  return (
    <span className={`paw ${className}`}>
      <i className="toe t1" />
      <i className="toe t2" />
      <i className="toe t3" />
      <i className="toe t4" />
      <i className="pad" />
    </span>
  )
}

/**
 * A faint Yale-spirit layer behind every page: oversized words that drift slowly, and a trail of
 * paw prints. It is purely decorative: it ignores the mouse and is hidden from screen readers.
 */
export default function Backdrop() {
  return (
    <div className="backdrop" aria-hidden="true">
      <span className="bg-word w-yale">YALE</span>
      <span className="bg-word w-boola">BOOLA BOOLA</span>
      <span className="bg-word w-lux">LUX ET VERITAS</span>
      <span className="bg-word w-year">1701</span>
      <Paw className="p1" />
      <Paw className="p2" />
      <Paw className="p3" />
      <Paw className="p4" />
      <Paw className="p5" />
      <Paw className="p6" />
    </div>
  )
}
