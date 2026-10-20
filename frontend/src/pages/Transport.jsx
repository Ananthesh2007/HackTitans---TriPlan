import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import Field, { inputClass } from '../components/Field.jsx'
import ResultsPanel from '../components/ResultsPanel.jsx'
import BookLink from '../components/BookLink.jsx'
import { useSearch } from '../hooks/useSearch.js'
import { searchTransport } from '../services/api.js'
import { todayString } from '../utils/dates.js'
import { cleanCount, cleanDate, cleanText } from '../utils/queryPrefill.js'
import { formatMoney } from '../utils/format.js'

const FIELD_ORDER = ['origin', 'destination', 'date', 'passengers']

const MODES = [
  { value: 'bus', label: 'Bus' },
  { value: 'train', label: 'Train' },
]

function initialValues(search) {
  const params = new URLSearchParams(search)
  return {
    mode: params.get('mode') === 'train' ? 'train' : 'bus',
    origin: cleanText(params.get('from')),
    destination: cleanText(params.get('to')),
    date: cleanDate(params.get('date')),
    passengers: String(cleanCount(params.get('passengers'), 1, 9, 1)),
  }
}

function validate(values) {
  const errors = {}
  const origin = values.origin.trim()
  const destination = values.destination.trim()

  if (origin.length < 2) errors.origin = 'Enter the place you are travelling from.'

  if (destination.length < 2) {
    errors.destination = 'Enter the place you are travelling to.'
  } else if (origin.toLowerCase() === destination.toLowerCase()) {
    errors.destination = 'Choose a different place from where you are travelling from.'
  }

  if (!values.date) {
    errors.date = 'Choose your travel date.'
  } else if (values.date < todayString()) {
    errors.date = 'Choose today or a later date.'
  }

  const passengers = Number(values.passengers)
  if (!Number.isInteger(passengers) || passengers < 1 || passengers > 9) {
    errors.passengers = 'Enter a whole number of passengers from 1 to 9.'
  }

  return errors
}

export default function Transport() {
  const { search: queryString } = useLocation()
  const [values, setValues] = useState(() => initialValues(queryString))
  const [errors, setErrors] = useState({})
  const [searchedMode, setSearchedMode] = useState(null)
  const [search, runSearch, retrySearch] = useSearch(searchTransport)
  const isSearching = search.status === 'loading'
  const modeLabel = values.mode === 'train' ? 'trains' : 'buses'

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

    setSearchedMode(values.mode)
    runSearch({
      mode: values.mode,
      origin: values.origin.trim(),
      destination: values.destination.trim(),
      date: values.date,
      passengers: Number(values.passengers),
    })
  }

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="headline-md">Buses and trains</h1>
      <p className="mt-2 max-w-xl text-muted">
        TriPlan shows bus and train options from travel providers. You book on the provider's own
        website. TriPlan does not take payment.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 max-w-xl space-y-6">
        <fieldset>
          <legend className="font-medium">Travel by</legend>
          <div className="mt-2 flex gap-6">
            {MODES.map(({ value, label }) => (
              <label key={value} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="mode"
                  value={value}
                  checked={values.mode === value}
                  onChange={handleChange}
                  className="size-4 accent-primary"
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="origin" label="From" error={errors.origin}>
            <input
              type="text"
              autoComplete="off"
              placeholder="City or town"
              className={inputClass(errors.origin)}
              {...fieldProps('origin')}
            />
          </Field>
          <Field id="destination" label="To" error={errors.destination}>
            <input
              type="text"
              autoComplete="off"
              placeholder="City or town"
              className={inputClass(errors.destination)}
              {...fieldProps('destination')}
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="date" label="Travel date" error={errors.date}>
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
          className="btn btn-primary"
        >
          {isSearching ? 'Searching...' : `Search ${modeLabel}`}
        </button>
      </form>

      {searchedMode === values.mode && (
        <ResultsPanel
          state={search}
          onRetry={retrySearch}
          emptyText={`No ${modeLabel} found. Try a different date or place.`}
        >
          {(results) => (
            <ul className="max-w-3xl divide-y divide-line border-y border-line">
              {results.map((option, index) => (
                <li key={option.id ?? index} className="py-4">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="font-medium">{option.operator || 'Operator not listed'}</p>
                    <p>
                      {typeof option.price === 'number'
                        ? `${formatMoney(option.price, option.currency)} per person`
                        : 'Price not available'}
                    </p>
                  </div>
                  <p className="mt-1 text-sm text-muted">
                    {[
                      typeof option.vehicle_type === 'string' ? option.vehicle_type : '',
                      option.departure_time && option.arrival_time
                        ? `${option.departure_time} to ${option.arrival_time}`
                        : '',
                      typeof option.duration === 'string' ? option.duration : '',
                    ]
                      .filter(Boolean)
                      .join(', ')}
                  </p>
                  <div className="mt-3">
                    <BookLink url={option.booking_url} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </ResultsPanel>
      )}
    </section>
  )
}