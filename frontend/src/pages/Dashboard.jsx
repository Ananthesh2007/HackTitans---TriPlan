import { useEffect, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { getTrip } from '../services/api.js'
import ItineraryCard from '../components/ItineraryCard.jsx'
import BudgetCard from '../components/BudgetCard.jsx'
import ChatAssistant from '../components/ChatAssistant.jsx'
import BookingOptions from '../components/BookingOptions.jsx'

function TripLoader({ tripId, initialTrip }) {
  const [state, setState] = useState(
    initialTrip
      ? { status: 'ready', trip: initialTrip, message: '' }
      : { status: 'loading', trip: null, message: '' },
  )
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    // A trip passed from the form is already loaded, so there is nothing to fetch.
    if (initialTrip) return undefined

    let cancelled = false

    getTrip(tripId)
      .then((trip) => {
        if (!cancelled) setState({ status: 'ready', trip, message: '' })
      })
      .catch((error) => {
        if (!cancelled) setState({ status: 'error', trip: null, message: error.message })
      })

    return () => {
      cancelled = true
    }
  }, [tripId, attempt, initialTrip])

  // Called when the user applies a change proposed by the assistant.
  function handleApply(trip) {
    setState({ status: 'ready', trip, message: '' })
  }

  function handleRetry() {
    setState({ status: 'loading', trip: null, message: '' })
    setAttempt((current) => current + 1)
  }

  if (state.status === 'loading') {
    return (
      <section className="mx-auto max-w-5xl px-4 py-12">
        <p role="status" className="text-muted">
          Loading your trip...
        </p>
      </section>
    )
  }

  if (state.status === 'error') {
    return (
      <section className="mx-auto max-w-5xl px-4 py-12">
        <h1 className="headline-md">We could not load this trip</h1>
        <p role="alert" className="mt-3 max-w-xl text-muted">
          {state.message}
        </p>
        <button
          type="button"
          onClick={handleRetry}
          className="btn btn-primary mt-6"
        >
          Try again
        </button>
      </section>
    )
  }

  const { trip } = state

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      {trip.is_mock && (
        <p className="mb-6 max-w-xl rounded-lg bg-card px-4 py-3 text-sm text-muted">
          Sample data for development. This is not a real plan.
        </p>
      )}

      <h1 className="headline-md">{trip.destination}</h1>
      <p className="mt-2 text-muted">
        {trip.days} {trip.days === 1 ? 'day' : 'days'}, {trip.people}{' '}
        {trip.people === 1 ? 'traveller' : 'travellers'}
      </p>
      <p className="mt-1 text-sm text-muted">Costs are estimates, not confirmed prices.</p>
      <p className="mt-3 flex flex-wrap gap-x-6 gap-y-1">
        <a href="#booking" className="btn-link text-accent">
          Book flights, buses, trains, and hotels
        </a>
        <a href="#assistant" className="btn-link text-accent">
          Ask the assistant to change this plan
        </a>
      </p>

      <div className="mt-8">
        <BudgetCard budget={trip.budget} costs={trip.estimated_costs} currency={trip.currency} />
      </div>

      <div className="mt-10 space-y-10">
        {trip.itinerary.map((day) => (
          <ItineraryCard key={day.day} day={day} currency={trip.currency} people={trip.people} />
        ))}
      </div>

      <div id="booking" className="mt-12 border-t border-line pt-8">
        <BookingOptions trip={trip} />
      </div>

      <div id="assistant" className="mt-12 border-t border-line pt-8">
        <ChatAssistant trip={trip} onApply={handleApply} />
      </div>
    </section>
  )
}

export default function Dashboard() {
  const { tripId } = useParams()
  const { state } = useLocation()
  // The key makes React start fresh when the trip id in the address changes.
  return <TripLoader key={tripId} tripId={tripId} initialTrip={state?.trip} />
}