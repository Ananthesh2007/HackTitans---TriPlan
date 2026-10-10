import { Link, NavLink } from 'react-router-dom'

const links = [
  { to: '/plan', label: 'Plan a trip' },
  { to: '/flights', label: 'Flights' },
  { to: '/hotels', label: 'Hotels' },
]

export default function Navbar() {
  return (
    <header className="border-b border-line">
      <nav className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4">
        <Link to="/" className="font-serif text-xl font-semibold text-ink">
          TriPlan
        </Link>
        <ul className="flex items-center gap-4 text-sm sm:gap-6 sm:text-base">
          {links.map(({ to, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  isActive ? 'font-semibold text-brand' : 'text-muted hover:text-ink'
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  )
}