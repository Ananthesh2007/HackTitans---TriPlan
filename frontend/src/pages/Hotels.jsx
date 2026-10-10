import { useState } from 'react'
import Field, { inputClass } from '../components/Field.jsx'
import ResultsPanel from '../components/ResultsPanel.jsx'
import BookLink from '../components/BookLink.jsx'
import { useSearch } from '../hooks/useSearch.js'
import { searchHotels } from '../services/api.js'
import { todayString } from '../utils/dates.js'
import { formatMoney } from '../utils/format.js'

const FIELD_ORDER = ['destination', 'checkIn', 'checkOut', 'guests']
const INITIAL_VALUES = { destination: '', checkIn: '', checkOut: '', guests: '1' }

function validate(values) {
  const errors = {}

  if (values.destination.trim().length < 2) {
    errors.destination = 'Enter the city or area you want to stay in.'
  }

  if (!values.checkIn) {
    errors.checkIn = 'Choose your check-in date.'
  } else if (values.checkIn < todayString()) {
    errors.checkIn = 'Choose today or a later date.'
  }

  if (!values.checkOut) {
    errors.checkOut = 'Choose your check-out date.'
  } else if (values.checkIn && values.checkOut <= values.checkIn) {
    errors.checkOut = 'Check-out must be after check-in.'
  }

  const guests = Number(values.guests)
  if (!Number.isInteger(guests) || guests < 1 || guests > 20) {
    errors.guests = 'Enter a whole number of guests from 1 to 20.'
  }

  return errors
}

export default function Hotels() {
  const [values, setValues] = useState(INITIAL_VALUES)
  const [errors, setErrors] = useState({})
  const [search, runSearch, retrySearch] = useSearch(searchHotels)
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
      destination: values.destination.trim(),
      check_in: values.checkIn,
      check_out: values.checkOut,
      guests: Number(values.guests),
    })
  }

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-3xl font-semibold">Hotels</h1>
      <p className="mt-2 max-w-xl text-muted">
        TriPlan shows hotel results from travel providers. You book on the provider's own website.
        TriPlan does not take payment.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 max-w-xl space-y-6">
        <Field id="destination" label="Destination" error={errors.destination}>
          <input
            type="text"
            autoComplete="off"
            placeholder="City or area"
            className={inputClass(errors.destination)}
            {...fieldProps('destination')}
          />
        </Field>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="checkIn" label="Check-in" error={errors.checkIn}>
            <input
              type="date"
              min={todayString()}
              className={inputClass(errors.checkIn)}
              {...fieldProps('checkIn')}
            />
          </Field>
          <Field id="checkOut" label="Check-out" error={errors.checkOut}>
            <input
              type="date"
              min={values.checkIn || todayString()}
              className={inputClass(errors.checkOut)}
              {...fieldProps('checkOut')}
            />
          </Field>
        </div>

        <Field id="guests" label="Guests" error={errors.guests}>
          <input
            type="number"
            min="1"
            max="20"
            inputMode="numeric"
            className={inputClass(errors.guests)}
            {...fieldProps('guests')}
          />
        </Field>

        <button
          type="submit"
          disabled={isSearching}
          className="rounded bg-brand px-5 py-3 font-medium text-white hover:bg-brand-dark disabled:opacity-60"
        >
          {isSearching ? 'Searching...' : 'Search hotels'}
        </button>
      </form>

      <ResultsPanel
        state={search}
        onRetry={retrySearch}
        emptyText="No hotels found. Try different dates or a different place."
      >
        {(results) => (
          <ul className="max-w-3xl divide-y divide-line border-y border-line">
            {results.map((hotel, index) => (
              <li key={hotel.id ?? index} className="py-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium">{hotel.name || 'Hotel name not listed'}</p>
                  <p>
                    {typeof hotel.price_per_night === 'number'
                      ? `${formatMoney(hotel.price_per_night, hotel.currency)} per night`
                      : 'Price not available'}
                  </p>
                </div>
                {typeof hotel.area === 'string' && hotel.area && (
                  <p className="mt-1 text-sm text-muted">{hotel.area}</p>
                )}
                <div className="mt-3">
                  <BookLink url={hotel.booking_url} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </ResultsPanel>
    </section>
  )
}