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
import { searchHotels } from '../services/api.js'
import { todayString } from '../utils/dates.js'
import { cleanCount, cleanDate, cleanText, cleanConcession } from '../utils/queryPrefill.js'
import { formatMoney } from '../utils/format.js'
import {
  DEFAULT_FILTERS,
  HOTEL_SORT_OPTIONS,
  concessionLabels,
  filtersFromParams,
  toApiFilters,
} from '../utils/filters.js'
import { applyFiltersAndSort } from '../utils/resultFilters.js'

const FIELD_ORDER = ['destination', 'checkIn', 'checkOut', 'guests']

// Starting values can come from the page address, for example /hotels?destination=Goa
function initialValues(search) {
  const params = new URLSearchParams(search)
  const checkIn = cleanDate(params.get('check_in'))
  const checkOut = cleanDate(params.get('check_out'))
  return {
    destination: cleanText(params.get('destination')),
    checkIn,
    checkOut: checkIn && checkOut > checkIn ? checkOut : '',
    guests: String(cleanCount(params.get('guests'), 1, 20, 1)),
    concession: cleanConcession(params.get('concession')),
  }
}

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
  const { search: queryString } = useLocation()
  const [values, setValues] = useState(() => initialValues(queryString))
  const [errors, setErrors] = useState({})
  const [filters, setFilters] = useState(() =>
    filtersFromParams(new URLSearchParams(queryString), HOTEL_SORT_OPTIONS),
  )
  const [search, runSearch, retrySearch] = useSearch(searchHotels)
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
      destination: values.destination.trim(),
      check_in: values.checkIn,
      check_out: values.checkOut,
      guests: Number(values.guests),
      concession: values.concession || null,
      filters: toApiFilters(filters),
    }
  }

  // A filter that widens the search needs fresh results from the server.
  useFilterRefresh(filters, values.concession, search.status !== 'idle', runSearch, buildParams)

  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="headline-md">Hotels</h1>
      <p className="mt-2 max-w-xl text-muted">
        TriPlan shows hotel results from travel providers. You book on the provider's own website.
        TriPlan does not take payment.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 max-w-xl space-y-6">
        <Field id="destination" label="Destination" error={errors.destination}>
          <PlaceInput
            id="destination"
            label="Destination"
            value={values.destination}
            onChange={(value) => handlePlaceChange('destination', value)}
            error={errors.destination}
            describedBy={errors.destination ? 'destination-error' : undefined}
            placeholder="City or area"
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

        <ConcessionSelect
          value={values.concession}
          onChange={(value) => setValues((current) => ({ ...current, concession: value }))}
        />

        <button
          type="submit"
          disabled={isSearching}
          className="btn btn-primary"
        >
          {isSearching ? 'Searching...' : 'Search hotels'}
        </button>
      </form>

      <FilterPanel
        filters={filters}
        onChange={handleFilterChange}
        onReset={resetFilters}
        timeLegend="Check-in time"
      />

      <ResultsPanel
        state={search}
        onRetry={retrySearch}
        emptyText="No hotels match these filters. Try different dates or a different place, or change a filter."
        results={visibleResults}
      >
        {() => (
          <>
            <SortSelect
              value={filters.sort}
              options={HOTEL_SORT_OPTIONS}
              onChange={(value) => handleFilterChange('sort', value)}
              resultCount={visibleResults.length}
            />

            <ul className="max-w-3xl divide-y divide-line border-y border-line">
              {visibleResults.map((hotel, index) => (
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
                  {hotel.check_in_time && (
                    <p className="mt-1 text-sm text-muted">
                      Check-in from {hotel.check_in_time}
                    </p>
                  )}
                  {Array.isArray(hotel.concessions) && hotel.concessions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="chip">
                        Concession: {concessionLabels(hotel.concessions)}
                      </span>
                    </div>
                  )}
                  <div className="mt-3">
                    <BookLink url={hotel.booking_url} />
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
