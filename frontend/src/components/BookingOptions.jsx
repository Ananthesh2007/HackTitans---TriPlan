import { Link } from 'react-router-dom'
import { addDays, formatDate, isDateString } from '../utils/dates.js'

function plural(count, word) {
  return `${count} ${word}${count === 1 ? '' : 's'}`
}

function buildLink(path, entries) {
  const params = new URLSearchParams()
  for (const [key, value] of entries) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  }
  const query = params.toString()
  return query ? `${path}?${query}` : path
}

// Shows where to book flights, buses, trains, and hotels for this trip.
// Each link opens the matching page with the trip's details already filled in.
export default function BookingOptions({ trip }) {
  const origin = typeof trip.origin === 'string' ? trip.origin : ''
  const destination = typeof trip.destination === 'string' ? trip.destination : ''
  const date = isDateString(trip.travel_date) ? trip.travel_date : ''
  const people = Number.isInteger(trip.people) && trip.people > 0 ? trip.people : 1
  const days = Number.isInteger(trip.days) && trip.days > 0 ? trip.days : trip.itinerary.length
  const checkOut = date && days > 0 ? addDays(date, days) : ''

  const travelEntries = [
    ['from', origin],
    ['to', destination],
    ['date', date],
    ['passengers', people],
  ]

  const route = origin ? `${origin} to ${destination}` : `To ${destination}`
  const travelSummary = [route, formatDate(date), plural(people, 'traveller')]
    .filter(Boolean)
    .join(', ')
  const stayDates = date ? `${formatDate(date)} to ${formatDate(checkOut)}` : ''
  const staySummary = [destination, stayDates, plural(people, 'guest')].filter(Boolean).join(', ')

  const options = [
    {
      title: 'Flights',
      summary: travelSummary,
      action: 'Find flights',
      to: buildLink('/flights', travelEntries),
    },
    {
      title: 'Buses',
      summary: travelSummary,
      action: 'Find buses',
      to: buildLink('/transport', [['mode', 'bus'], ...travelEntries]),
    },
    {
      title: 'Trains',
      summary: travelSummary,
      action: 'Find trains',
      to: buildLink('/transport', [['mode', 'train'], ...travelEntries]),
    },
    {
      title: 'Hotels',
      summary: staySummary,
      action: 'Find hotels',
      to: buildLink('/hotels', [
        ['destination', destination],
        ['check_in', date],
        ['check_out', checkOut],
        ['guests', people],
      ]),
    },
  ]

  return (
    <section aria-labelledby="booking-heading" className="max-w-3xl">
      <h2 id="booking-heading" className="text-xl font-black">
        Book your trip
      </h2>
      <p className="mt-2 text-sm text-muted">
        TriPlan shows options from travel providers. You book on the provider's own website.
        TriPlan does not take payment.
      </p>

      <ul className="mt-4 divide-y divide-line border-y border-line">
        {options.map((option) => (
          <li
            key={option.title}
            className="flex flex-wrap items-center justify-between gap-3 py-4"
          >
            <div>
              <h3 className="font-medium">{option.title}</h3>
              <p className="text-sm text-muted">{option.summary}</p>
            </div>
            <Link
              to={option.to}
              className="btn btn-secondary btn-sm"
            >
              {option.action}
              <span className="sr-only"> for this trip</span>
            </Link>
          </li>
        ))}
      </ul>

      {!origin && (
        <p className="mt-3 text-sm text-muted">
          You will enter where you are travelling from on the next page.
        </p>
      )}
    </section>
  )
}