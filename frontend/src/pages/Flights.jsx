import { useState } from 'react'
import Field, { inputClass } from '../components/Field.jsx'
import ResultsPanel from '../components/ResultsPanel.jsx'
import BookLink from '../components/BookLink.jsx'
import { useSearch } from '../hooks/useSearch.js'
import { searchFlights } from '../services/api.js'
import { todayString } from '../utils/dates.js'
import { formatMoney } from '../utils/format.js'

const FIELD_ORDER = ['origin', 'destination', 'date', 'passengers']
const INITIAL_VALUES = { origin: '', destination: '', date: '', passengers: '1' }

function validate(values) {
  const errors = {}
  const origin = values.origin.trim()
  const destination = values.destination.trim()

  if (origin.length < 2) errors.origin = 'Enter the city or airport you are flying from.'

  if (destination.length < 2) {
    errors.destination = 'Enter the city or airport you are flying to.'
  } else if (origin.toLowerCase() === destination.toLowerCase()) {
    errors.destination = 'Choose a different place from where you are flying from.'
  }

  if (!values.date) {
    errors.date = 'Choose your departure date.'
  } else if (values.date < todayString()) {
    errors.date = 'Choose today or a later date.'
  }

  const passengers = Number(values.passengers)
  if (!Number.isInteger(passengers) || passengers < 1 || passengers > 9) {
    errors.passengers = 'Enter a whole number of passengers from 1 to 9.'
  }

  return errors
}

function stopsText(stops) {
  if (stops === 0) return 'Non-stop'
  if (Number.isInteger(stops) && stops > 0) return `${stops} ${stops === 1 ? 'stop' : 'stops'}`
  return ''
}

export default function Flights() {
  const [values, setValues] = useState(INITIAL_VALUES)
  const [errors, setErrors] = useState({})
  const [search, runSearch, retrySearch] = useSearch(searchFlights)
  const isSearching = search.status === 'loading'

  function handleChange(event) {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    if (errors[name]) setErrors((current) => ({ ...current, [name]: undefined }))
  }

  function fieldProps(name) {
    return {
      id: name,
      name,
      value: values[name],
      onChange: handleChange,
      'aria-invalid': errors[name] ? 'true' : 'false',
      'aria-describedby': errors[name] ? `${name}-error` : undefined,
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    if (isSearching) return

    const nextErrors = validate(values)
    setErrors(nextErrors)
    const firstInvalid = FIELD_ORDER.find((name) => nextErrors[name])
    if (firstInvalid) {
      document.getElementById(firstInvalid)?.focus()
      return
    }

    runSearch({
      origin: values.origin.trim(),
      destination: values.destination.trim(),
      date: values.date,
      passengers: Number(values.passengers),
    })
  }

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-3xl font-semibold">Flights</h1>
      <p className="mt-2 max-w-xl text-muted">
        TriPlan shows flight results from travel providers. You book on the provider's own
        website. TriPlan does not take payment.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 max-w-xl space-y-6">
        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="origin" label="From" error={errors.origin}>
            <input
              type="text"
              autoComplete="off"
              placeholder="City or airport"
              className={inputClass(errors.origin)}
              {...fieldProps('origin')}
            />
          </Field>
          <Field id="destination" label="To" error={errors.destination}>
            <input
              type="text"
              autoComplete="off"
              placeholder="City or airport"
              className={inputClass(errors.destination)}
              {...fieldProps('destination')}
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="date" label="Departure date" error={errors.date}>
            <input
              type="date"
              min={todayString()}
              className={inputClass(errors.date)}
              {...fieldProps('date')}
            />
          </Field>
          <Field id="passengers" label="Passengers" error={errors.passengers}>
            <input
              type="number"
              min="1"
              max="9"
              inputMode="numeric"
              className={inputClass(errors.passengers)}
              {...fieldProps('passengers')}
            />
          </Field>
        </div>

        <button
          type="submit"
          disabled={isSearching}
          className="rounded bg-brand px-5 py-3 font-medium text-white hover:bg-brand-dark disabled:opacity-60"
        >
          {isSearching ? 'Searching...' : 'Search flights'}
        </button>
      </form>

      <ResultsPanel
        state={search}
        onRetry={retrySearch}
        emptyText="No flights found. Try a different date or place."
      >
        {(results) => (
          <ul className="max-w-3xl divide-y divide-line border-y border-line">
            {results.map((flight, index) => (
              <li key={flight.id ?? index} className="py-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium">{flight.airline || 'Airline not listed'}</p>
                  <p>
                    {typeof flight.price === 'number'
                      ? `${formatMoney(flight.price, flight.currency)} per person`
                      : 'Price not available'}
                  </p>
                </div>
                <p className="mt-1 text-sm text-muted">
                  {[
                    flight.departure_time && flight.arrival_time
                      ? `${flight.departure_time} to ${flight.arrival_time}`
                      : '',
                    typeof flight.duration === 'string' ? flight.duration : '',
                    stopsText(flight.stops),
                  ]
                    .filter(Boolean)
                    .join(', ')}
                </p>
                <div className="mt-3">
                  <BookLink url={flight.booking_url} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </ResultsPanel>
    </section>
  )
}