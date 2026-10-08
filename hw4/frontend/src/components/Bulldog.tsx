import { useEffect, useRef, useState } from 'react'

const PHRASES = ['Boola Boola!', 'Woof!', 'Go Bulldogs!', 'Lux et Veritas!', 'Bright College Years!']

interface Props {
  className?: string
}

/**
 * Handsome Dan, the Yale bulldog. He is built from plain HTML elements styled with CSS (no image
 * and no drawing), blinks, pants, and barks a Yale cheer when clicked.
 */
export default function Bulldog({ className = '' }: Props) {
  const [barks, setBarks] = useState(0)
  const [phrase, setPhrase] = useState<string | null>(null)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(timer.current), [])

  function bark() {
    setPhrase(PHRASES[barks % PHRASES.length])
    setBarks((n) => n + 1)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setPhrase(null), 2300)
  }

  return (
    <button
      type="button"
      className={`bulldog${phrase ? ' barking' : ''} ${className}`.trim()}
      onClick={bark}
      aria-label="Handsome Dan, the Yale bulldog. Click to hear him bark."
    >
      {phrase && (
        <span className="bd-speech" role="status" key={barks}>
          {phrase}
        </span>
      )}
      <span className="bd-ear left" aria-hidden="true" />
      <span className="bd-ear right" aria-hidden="true" />
      <span className="bd-head" aria-hidden="true" />
      <span className="bd-patch" aria-hidden="true" />
      <span className="bd-wrinkle w1" aria-hidden="true" />
      <span className="bd-wrinkle w2" aria-hidden="true" />
      <span className="bd-eye left" aria-hidden="true" />
      <span className="bd-eye right" aria-hidden="true" />
      <span className="bd-brow left" aria-hidden="true" />
      <span className="bd-brow right" aria-hidden="true" />
      <span className="bd-snout" aria-hidden="true" />
      <span className="bd-jowl left" aria-hidden="true" />
      <span className="bd-jowl right" aria-hidden="true" />
      <span className="bd-tongue" aria-hidden="true" />
      <span className="bd-smile left" aria-hidden="true" />
      <span className="bd-smile right" aria-hidden="true" />
      <span className="bd-tooth left" aria-hidden="true" />
      <span className="bd-tooth right" aria-hidden="true" />
      <span className="bd-nose" aria-hidden="true" />
      <span className="bd-mouth" aria-hidden="true" />
      <span className="bd-collar" aria-hidden="true">
        <span className="bd-tag">Y</span>
      </span>
    </button>
  )
}
