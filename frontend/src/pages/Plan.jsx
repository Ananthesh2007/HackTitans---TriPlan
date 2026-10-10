import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TripForm from '../components/TripForm.jsx'
import { createTrip } from '../services/api.js'

export default function Plan() {
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  async function handleSubmit(tripRequest) {
    if (isSubmitting) return
    setIsSubmitting(true)
    setErrorMessage('')

    try {
      const trip = await createTrip(tripRequest)
      // Pass the trip along so the dashboard does not need to fetch it again.
      navigate(`/trips/${encodeURIComponent(trip.trip_id)}`, { state: { trip } })
    } catch (error) {
      setErrorMessage(error.message)
      setIsSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-3xl font-semibold">Plan a trip</h1>
      <p className="mt-2 max-w-xl text-muted">
        Enter the basics. You can change the plan afterwards by chatting with the assistant.
      </p>

      <div className="mt-8 max-w-xl">
        <TripForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />

        {isSubmitting && (
          <p role="status" className="mt-4 text-muted">
            Building your itinerary. This can take a little while.
          </p>
        )}

        {errorMessage && (
          <div role="alert" className="mt-4 border border-red-700 bg-white px-4 py-3">
            <p className="font-medium text-red-700">We could not create your trip.</p>
            <p className="mt-1 text-sm">{errorMessage}</p>
            <p className="mt-1 text-sm text-muted">
              Your details are still in the form. Check them and select Generate itinerary again.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}