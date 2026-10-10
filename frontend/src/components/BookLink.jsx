import { isSafeBookingUrl } from '../utils/url.js'

// Opens the provider's own website in a new tab. TriPlan never takes payment.
export default function BookLink({ url }) {
  if (!isSafeBookingUrl(url)) {
    return <p className="text-sm text-muted">No booking link for this result.</p>
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-block rounded bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark"
    >
      Book on the provider's site
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  )
}