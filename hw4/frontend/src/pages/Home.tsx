import { Link } from 'react-router-dom'
import Bulldog from '../components/Bulldog'

export default function Home() {
  return (
    <section className="hero">
      <Bulldog className="hero-dog" />
      <h1>
        Authentic <span className="accent">Campus Apparel</span> &amp; Custom Gear
      </h1>
      <p>
        Show your campus pride with premium quality gear, custom merchandise, and official
        apparel. Designed for students, alumni, and fans.
      </p>
      <Link to="/products" className="button">
        Shop Products
      </Link>
    </section>
  )
}
