const ITEMS = [
  'Go Bulldogs!',
  'Boola Boola',
  'Lux et Veritas',
  'Handsome Dan',
  'Est. 1701',
  'Bright College Years',
  'The Game',
]

/** A slow, endless banner of Yale cheers under the navbar. It is decoration only. */
export default function Ticker() {
  // The list is written out twice so the loop can slide by exactly half its width, seamlessly.
  const run = [...ITEMS, ...ITEMS]
  return (
    <div className="ticker" aria-hidden="true">
      <div className="ticker-track">
        {[0, 1].map((copy) => (
          <div className="ticker-run" key={copy}>
            {run.map((text, i) => (
              <span className="ticker-item" key={i}>
                <span className="ticker-star">★</span> {text}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
