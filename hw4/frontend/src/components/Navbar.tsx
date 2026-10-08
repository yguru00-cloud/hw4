import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'

const links = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const guestLinks = [
  { to: '/login', label: 'Log in' },
  { to: '/register', label: 'Create account' },
]

export default function Navbar() {
  const { user, loading, logout } = useAuth()
  const { clearResults } = useChatResults()

  const renderLink = (link: { to: string; label: string }) => (
    <NavLink
      key={link.to}
      to={link.to}
      end={link.to === '/'}
      className={({ isActive }) => (isActive ? 'active' : undefined)}
    >
      {link.label}
    </NavLink>
  )

  return (
    <header className="navbar">
      <NavLink to="/" className="brand">
        Campus<span>Customs</span>
      </NavLink>
      <nav>
        {links.map(renderLink)}
        {loading ? null : user ? (
          <>
            <span className="nav-user">Hi, {user.first_name || user.email}</span>
            <button
              type="button"
              className="nav-button"
              onClick={() => {
                clearResults() // the previous customer's search results should not stay on screen
                void logout()
              }}
            >
              Log out
            </button>
          </>
        ) : (
          guestLinks.map(renderLink)
        )}
      </nav>
    </header>
  )
}
