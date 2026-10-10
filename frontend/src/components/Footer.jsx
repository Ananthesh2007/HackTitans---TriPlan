import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted">
        <p>Costs shown on TriPlan are estimates, not confirmed prices.</p>
        <ul className="flex gap-4">
          <li>
            <Link to="/privacy" className="hover:text-ink">
              Privacy Policy
            </Link>
          </li>
          <li>
            <Link to="/terms" className="hover:text-ink">
              Terms and Conditions
            </Link>
          </li>
        </ul>
      </div>
    </footer>
  )
}