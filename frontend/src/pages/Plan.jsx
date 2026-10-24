import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import TripForm from '../components/TripForm.jsx'
import { createTrip } from '../services/api.js'
import { fadeInProps } from '../lib/motion.js'

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
    <motion.section
      {...fadeInProps}
      className="mx-auto max-w-5xl px-4 py-12"
    >
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="headline-md text-slate-100"
      >
        Plan a trip
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-2 max-w-xl text-slate-400"
      >
        Enter the basics. You can change the plan afterwards by chatting with the assistant.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-8 max-w-xl glass-panel p-8"
      >
        <TripForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />

        <AnimatePresence mode="wait">
          {isSubmitting && (
            <motion.p
              key="submitting"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              role="status"
              className="mt-4 text-slate-400"
            >
              Building your itinerary. This can take a little while.
            </motion.p>
          )}

          {errorMessage && (
            <motion.div
              key="error"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              role="alert"
              className="glass-panel mt-4 border border-error p-4"
            >
              <p className="font-medium text-error">We could not create your trip.</p>
              <p className="mt-1 text-sm text-slate-300">{errorMessage}</p>
              <p className="mt-1 text-sm text-slate-400">
                Your details are still in the form. Check them and select Generate itinerary again.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.section>
  )
}