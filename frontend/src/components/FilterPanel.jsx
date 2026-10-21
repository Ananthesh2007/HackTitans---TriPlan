import { useState } from 'react'
import {
  AC_OPTIONS,
  DEPARTURE_OPTIONS,
  SEAT_OPTIONS,
  countActiveFilters,
} from '../utils/filters.js'

// The filters for a search page.
//
// The panel is always visible on a wide screen. On a narrow one it folds
// away behind a button, so the form does not push the results off the
// screen. The filters always work: they are applied to the results that
// are already on the page, so they take effect straight away.

// A group of radio buttons.
function RadioGroup({ legend, name, options, value, onChange, columns = 2 }) {
  return (
    <fieldset>
      <legend className="label-md">{legend}</legend>
      <div
        className={`mt-2 grid gap-2 ${
          columns === 3 ? 'grid-cols-3' : 'grid-cols-2 sm:grid-cols-4'
        }`}
      >
        {options.map((option) => (
          <label
            key={option.value}
            className="flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm"
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="size-4 accent-primary"
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

// A group of checkboxes.
function CheckGroup({ legend, name, options, values, onToggle }) {
  return (
    <fieldset>
      <legend className="label-md">{legend}</legend>
      <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {options.map((option) => (
          <label
            key={option.value}
            className="flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm"
          >
            <input
              type="checkbox"
              name={name}
              value={option.value}
              checked={values.includes(option.value)}
              onChange={() => onToggle(option.value)}
              className="size-4 accent-primary"
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

// The price range: two numbers, a lowest and a highest.
function PriceRange({ filters, onChange }) {
  return (
    <fieldset>
      <legend className="label-md">Price range (INR)</legend>
      <div className="mt-2 grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="priceMin" className="block text-sm text-muted">
            Lowest
          </label>
          <input
            type="number"
            id="priceMin"
            name="priceMin"
            min="0"
            step="50"
            inputMode="numeric"
            placeholder="No minimum"
            value={filters.priceMin}
            onChange={(event) => onChange('priceMin', event.target.value)}
            className="input mt-1"
          />
        </div>
        <div>
          <label htmlFor="priceMax" className="block text-sm text-muted">
            Highest
          </label>
          <input
            type="number"
            id="priceMax"
            name="priceMax"
            min="0"
            step="50"
            inputMode="numeric"
            placeholder="No maximum"
            value={filters.priceMax}
            onChange={(event) => onChange('priceMax', event.target.value)}
            className="input mt-1"
          />
        </div>
      </div>
    </fieldset>
  )
}

// The panel that holds every filter for a search page.
//
// `showVehicle` adds the AC and seat class filters, which only make sense
// for buses and trains. `showNew` adds the "new vehicles only" filter, and
// `showTracking` adds the "live tracking only" filter.
export default function FilterPanel({
  filters,
  onChange,
  onToggle,
  onReset,
  showVehicle = false,
  showTracking = false,
  showNew = false,
  timeLegend = 'Departure time',
}) {
  const [isOpen, setIsOpen] = useState(false)
  const activeCount = countActiveFilters(filters)

  const serviceOptions = [
    ...(showTracking ? [{ value: 'tracking', label: 'Live tracking only' }] : []),
    ...(showNew ? [{ value: 'isNew', label: 'New vehicles only' }] : []),
  ]

  const serviceValues = [
    ...(showTracking && filters.tracking ? ['tracking'] : []),
    ...(showNew && filters.isNew ? ['isNew'] : []),
  ]

  return (
    <section aria-labelledby="filters-heading" className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="filters-heading" className="headline-sm">
          Filters
          {activeCount > 0 && (
            <span className="ml-2 text-sm font-normal text-muted">
              {activeCount} {activeCount === 1 ? 'filter' : 'filters'} on
            </span>
          )}
        </h2>

        <button
          type="button"
          onClick={() => setIsOpen((current) => !current)}
          aria-expanded={isOpen}
          aria-controls="filters-body"
          className="btn btn-secondary btn-sm sm:hidden"
        >
          {isOpen ? 'Hide filters' : `Filters${activeCount > 0 ? ` (${activeCount})` : ''}`}
        </button>
      </div>

      <div id="filters-body" className={`mt-4 ${isOpen ? 'block' : 'hidden sm:block'}`}>
        <div className="panel space-y-6">
          {showVehicle && (
            <RadioGroup
              legend="AC"
              name="ac-filter"
              options={AC_OPTIONS}
              value={filters.ac}
              onChange={(value) => onChange('ac', value)}
            />
          )}

          {showVehicle && (
            <RadioGroup
              legend="Seat type"
              name="seat-filter"
              options={SEAT_OPTIONS}
              value={filters.seatClass}
              onChange={(value) => onChange('seatClass', value)}
            />
          )}

          {serviceOptions.length > 0 && (
            <CheckGroup
              legend="Service"
              name="service-filter"
              options={serviceOptions}
              values={serviceValues}
              onToggle={onToggle}
            />
          )}

          <PriceRange filters={filters} onChange={onChange} />

          <RadioGroup
            legend={timeLegend}
            name="departure-filter"
            options={DEPARTURE_OPTIONS}
            value={filters.departureWindow}
            onChange={(value) => onChange('departureWindow', value)}
            columns={3}
          />

          {activeCount > 0 && (
            <button type="button" onClick={onReset} className="btn btn-secondary btn-sm">
              Clear all filters
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
