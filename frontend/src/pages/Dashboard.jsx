import { useEffect, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { getTrip, getTripMap } from '../services/api.js'
import ItineraryCard from '../components/ItineraryCard.jsx'
import BudgetCard from '../components/BudgetCard.jsx'
import ChatAssistant from '../components/ChatAssistant.jsx'
import BookingOptions from '../components/BookingOptions.jsx'
import MapView from '../components/MapView.jsx'
import { staggerContainer, staggerItem } from '../lib/motion.js'

function TripLoader({ tripId, initialTrip }) {
  const [state, setState] = useState(
    initialTrip
      ? { status: 'ready', trip: initialTrip, message: '' }
      : { status: 'loading', trip: null, message: '' },
  )
  const [attempt, setAttempt] = useState(0)
  // The map is loaded on its own, so a slow or failing map never blocks the plan.
  const [mapState, setMapState] = useState({ status: 'loading', map: null, message: '' })

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

  // The map is fetched separately from the trip, so a maps problem never
  // stops the itinerary from showing. The version is bumped when the plan
  // changes, so the map is rebuilt for the new places.
  const [mapVersion, setMapVersion] = useState(0)

  useEffect(() => {
    let cancelled = false

    getTripMap(tripId)
      .then((map) => {
        if (!cancelled) setMapState({ status: 'ready', map, message: '' })
      })
      .catch((error) => {
        if (!cancelled) setMapState({ status: 'error', map: null, message: error.message })
      })

    return () => {
      cancelled = true
    }
  }, [tripId, mapVersion])

  // Called when the user applies a change proposed by the assistant.
  function handleApply(trip) {
    setState({ status: 'ready', trip, message: '' })
    // The places may have changed, so the map is fetched again.
    setMapState({ status: 'loading', map: null, message: '' })
    setMapVersion((current) => current + 1)
  }

  function handleRetry() {
    setState({ status: 'loading', trip: null, message: '' })
    setAttempt((current) => current + 1)
  }

  if (state.status === 'loading') {
    return (
      <section className="mx-auto max-w-5xl px-4 py-12">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="headline-md text-slate-100"
        >
          Building your itinerary...
        </motion.h1>
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="mt-6 space-y-4 max-w-md"
        >
          <motion.div variants={staggerItem} className="flex items-center gap-3">
            <motion.div
              className="h-4 w-4 rounded-full bg-primary"
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.6, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <p className="text-sm font-medium text-slate-100">Analyzing travel preferences and destination...</p>
          </motion.div>
          <motion.div variants={staggerItem} className="flex items-center gap-3">
            <motion.div
              className="h-4 w-4 rounded-full bg-accent"
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.6, 1] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
            />
            <p className="text-sm text-slate-400">Structuring day-by-day activities and routes...</p>
          </motion.div>
          <motion.div variants={staggerItem} className="flex items-center gap-3">
            <motion.div
              className="h-4 w-4 rounded-full bg-secondary"
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.6, 1] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
            />
            <p className="text-sm text-slate-400">Calculating real-time estimates and budgets...</p>
          </motion.div>
        </motion.div>
      </section>
    )
  }

  if (state.status === 'error') {
    return (
      <section className="mx-auto max-w-5xl px-4 py-12">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="headline-md text-slate-100"
        >
          We could not load this trip
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          role="alert"
          className="mt-3 max-w-xl text-slate-400"
        >
          {state.message}
        </motion.p>
        <motion.button
          type="button"
          onClick={handleRetry}
          className="btn btn-primary mt-6"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          Try again
        </motion.button>
      </section>
    )
  }

  const { trip } = state

  return (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="mx-auto max-w-5xl px-4 py-12"
    >
      {trip.is_mock && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 max-w-xl glass-panel px-4 py-3 text-sm text-slate-400"
        >
          Sample data for development. This is not a real plan.
        </motion.p>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="headline-md text-slate-100">{trip.destination}</h1>
        <p className="mt-2 text-slate-400">
          {trip.days} {trip.days === 1 ? 'day' : 'days'}, {trip.people}{' '}
          {trip.people === 1 ? 'traveller' : 'travellers'}
        </p>
        <p className="mt-1 text-sm text-slate-400">Costs are estimates, not confirmed prices.</p>
        <motion.p
          className="mt-3 flex flex-wrap gap-x-6 gap-y-1"
          variants={staggerContainer}
          initial="hidden"
          animate="show"
        >
          <motion.a variants={staggerItem} href="#map" className="btn-link text-accent">
            See the plan on a map
          </motion.a>
          <motion.a variants={staggerItem} href="#booking" className="btn-link text-accent">
            Book flights, buses, trains, and hotels
          </motion.a>
          <motion.a variants={staggerItem} href="#assistant" className="btn-link text-accent">
            Ask the assistant to change this plan
          </motion.a>
        </motion.p>
      </motion.div>

      <div className="mt-8">
        <BudgetCard budget={trip.budget} costs={trip.estimated_costs} currency={trip.currency} />
      </div>

      <div id="map" className="mt-10">
        <MapView
          map={mapState.map}
          isLoading={mapState.status === 'loading'}
          error={mapState.status === 'error' ? mapState.message : ''}
        />
      </div>

      <motion.div
        className="mt-10 space-y-6"
        variants={staggerContainer}
        initial="hidden"
        animate="show"
      >
        {trip.itinerary.map((day) => (
          <ItineraryCard key={day.day} day={day} currency={trip.currency} people={trip.people} />
        ))}
      </motion.div>

      <div id="booking" className="mt-12 border-t border-line pt-8">
        <BookingOptions trip={trip} />
      </div>

      <div id="assistant" className="mt-12 border-t border-line pt-8">
        <ChatAssistant trip={trip} onApply={handleApply} />
      </div>
    </motion.section>
  )
}

export default function Dashboard() {
  const { tripId } = useParams()
  const { state } = useLocation()
  // The key makes React start fresh when the trip id in the address changes.
  return <TripLoader key={tripId} tripId={tripId} initialTrip={state?.trip} />
}