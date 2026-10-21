import { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import Field, { inputClass } from '../components/Field.jsx'
import ResultsPanel from '../components/ResultsPanel.jsx'
import BookLink from '../components/BookLink.jsx'
import PlaceInput from '../components/PlaceInput.jsx'
import ConcessionSelect from '../components/ConcessionSelect.jsx'
import FilterPanel from '../components/FilterPanel.jsx'
import SortSelect from '../components/SortSelect.jsx'
import { useSearch } from '../hooks/useSearch.js'
import { useFilterRefresh } from '../hooks/useFilterRefresh.js'
import { searchFlights } from '../services/api.js'
import { todayString } from '../utils/dates.js'
import { cleanCount, cleanDate, cleanText, cleanConcession } from '../utils/queryPrefill.js'
import { formatMoney } from '../utils/format.js'
import {
  DEFAULT_FILTERS,
  SORT_OPTIONS,
  concessionLabels,
  filtersFromParams,
  toApiFilters,
} from '../utils/filters.js'
import { applyFiltersAndSort } from '../utils/resultFilters.js'

const FIELD_ORDER = ['origin', 'destination', 'date', 'passengers']

// Starting values can come from the page address, for example /flights?from=Pune&to=Goa
function initialValues(search) {
  const params = new URLSearchParams(search)
  return {
    origin: cleanText(params.get('from')),
    destination: cleanText(params.get('to')),
    date: cleanDate(params.get('date')),
    passengers: String(cleanCount(params.get('passengers'), 1, 9, 1)),
    concession: cleanConcession(params.get('concession')),
  }
}

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
  const { search: queryString } = useLocation()
  const [values, setValues] = useState(() => initialValues(queryString))
  const [errors, setErrors] = useState({})
  const [filters, setFilters] = useState(() => filtersFromParams(new URLSearchParams(queryString)))
  const [search, runSearch, retrySearch] = useSearch(searchFlights)
  const isSearching = search.status === 'loading'

  // The results as they came back, before the filters are applied.
  const rawResults = useMemo(() => search.data?.results || [], [search.data])

  // The results the user sees: filtered and sorted on this page, so a
  // filter takes effect straight away.
  const visibleResults = useMemo(
    () => applyFiltersAndSort(rawResults, filters, values.concession),
    [rawResults, filters, values.concession],
  )

  function handleChange(event) {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    if (errors[name]) setErrors((current) => ({ ...current, [name]: undefined }))
  }

  function handlePlaceChange(name, value) {
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

  function handleFilterChange(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
  }

  function resetFilters() {
    setFilters({ ...DEFAULT_FILTERS })
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

    runSearch(buildParams())
  }

  // The request the search sends.
  function buildParams() {
    return {
      origin: values.origin.trim(),
      destination: values.destination.trim(),
      date: values.date,
      passengers: Number(values.passengers),
      concession: values.concession || null,
      filters: toApiFilters(filters),
    }
  }

  // A filter that widens the search needs fresh results from the server.
  useFilterRefresh(filters, values.concession, search.status !== 'idle', runSearch, buildParams)

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="headline-md">Flights</h1>
      <p className="mt-2 max-w-xl text-muted">
        TriPlan shows flight results from travel providers. You book on the provider's own
        website. TriPlan does not take payment.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 max-w-xl space-y-6">
        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="origin" label="From" error={errors.origin}>
            <PlaceInput
              id="origin"
              label="From"
              value={values.origin}
              onChange={(value) => handlePlaceChange('origin', value)}
              error={errors.origin}
              describedBy={errors.origin ? 'origin-error' : undefined}
              placeholder="City or airport"
            />
          </Field>
          <Field id="destination" label="To" error={errors.destination}>
            <PlaceInput
              id="destination"
              label="To"
              value={values.destination}
              onChange={(value) => handlePlaceChange('destination', value)}
              error={errors.destination}
              describedBy={errors.destination ? 'destination-error' : undefined}
              placeholder="City or airport"
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

        <ConcessionSelect
          value={values.concession}
          onChange={(value) => setValues((current) => ({ ...current, concession: value }))}
        />

        <button
          type="submit"
          disabled={isSearching}
          className="btn btn-primary"
        >
          {isSearching ? 'Searching...' : 'Search flights'}
        </button>
      </form>

      <FilterPanel
        filters={filters}
        onChange={handleFilterChange}
        onReset={resetFilters}
        timeLegend="Departure time"
      />

      <ResultsPanel
        state={search}
        onRetry={retrySearch}
        emptyText="No flights match these filters. Try a different date or place, or change a filter."
        results={visibleResults}
      >
        {() => (
          <>
            <SortSelect
              value={filters.sort}
              options={SORT_OPTIONS}
              onChange={(value) => handleFilterChange('sort', value)}
              resultCount={visibleResults.length}
            />

            <ul className="max-w-3xl divide-y divide-line border-y border-line">
              {visibleResults.map((flight, index) => (
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
                  {Array.isArray(flight.concessions) && flight.concessions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="chip">
                        Concession: {concessionLabels(flight.concessions)}
                      </span>
                    </div>
                  )}
                  <div className="mt-3">
                    <BookLink url={flight.booking_url} />
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </ResultsPanel>
    </section>
  )
}
