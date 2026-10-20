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
      className="btn btn-primary btn-sm"
    >
      Book on the provider's site
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  )
}