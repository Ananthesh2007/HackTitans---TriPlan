// The filters the user can pick on a search page.
//
// The same rules are applied in the backend (`backend/app/services/filters.py`),
// so a result is filtered the same way whether the page filters it or the
// server does. The rules are written twice on purpose: the backend has no
// JavaScript, and the frontend has no Python.

// The concession categories. The value is what the API uses.
export const CONCESSIONS = [
  { value: 'senior_citizen', label: 'Senior citizen' },
  { value: 'army', label: 'Army' },
  { value: 'student', label: 'Student' },
  { value: 'doctor', label: 'Doctor' },
  { value: 'nurse', label: 'Nurse' },
]

// The AC filter, for buses and trains.
export const AC_OPTIONS = [
  { value: 'any', label: 'Any' },
  { value: 'ac', label: 'AC' },
  { value: 'non_ac', label: 'Non-AC' },
]

// The seat class filter, for buses and trains.
export const SEAT_OPTIONS = [
  { value: 'any', label: 'Any' },
  { value: 'seater', label: 'Seater' },
  { value: 'sleeper', label: 'Sleeper' },
]

// The time of day filter.
export const DEPARTURE_OPTIONS = [
  { value: 'any', label: 'Any time' },
  { value: 'night', label: 'Night (12am - 6am)' },
  { value: 'morning', label: 'Morning (6am - 12pm)' },
  { value: 'afternoon', label: 'Afternoon (12pm - 6pm)' },
  { value: 'evening', label: 'Evening (6pm - 12am)' },
]

// The sort options. "recommended" keeps the order the provider sent.
export const SORT_OPTIONS = [
  { value: 'recommended', label: 'Recommended' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
  { value: 'departure_asc', label: 'Departure: earliest first' },
  { value: 'departure_desc', label: 'Departure: latest first' },
  { value: 'duration_asc', label: 'Shortest trip first' },
]

// The sort options for hotels, which have no departure time.
export const HOTEL_SORT_OPTIONS = [
  { value: 'recommended', label: 'Recommended' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
  { value: 'name_asc', label: 'Name: A to Z' },
]

// The label of a concession category.
export function concessionLabel(value) {
  const option = CONCESSIONS.find((item) => item.value === value)
  return option ? option.label : value
}

// The labels of several concession categories, for a result that lists them.
export function concessionLabels(values) {
  if (!Array.isArray(values)) return ''
  return values.map(concessionLabel).join(', ')
}

// The filters every search page starts with.
export const DEFAULT_FILTERS = {
  ac: 'any',
  seatClass: 'any',
  tracking: false,
  isNew: false,
  priceMin: '',
  priceMax: '',
  departureWindow: 'any',
  sort: 'recommended',
}

// The filters as the API wants them. Empty values are left out, so the
// backend never has to guess what a blank price means.
export function toApiFilters(filters) {
  const api = {
    ac: filters.ac ?? 'any',
    seat_class: filters.seatClass ?? 'any',
    tracking: Boolean(filters.tracking),
    is_new: Boolean(filters.isNew),
    departure_window: filters.departureWindow ?? 'any',
    sort: filters.sort ?? 'recommended',
  }

  const min = Number(filters.priceMin)
  const max = Number(filters.priceMax)

  if (Number.isFinite(min) && min > 0) api.price_min = min
  if (Number.isFinite(max) && max > 0) api.price_max = max

  return api
}

// The filters as they are read from the page address.
export function filtersFromParams(params, sortOptions = SORT_OPTIONS) {
  const read = (key, allowed, fallback) => {
    const value = params.get(key)
    return allowed.includes(value) ? value : fallback
  }

  const flag = (key) => params.get(key) === 'true'

  return {
    ac: read('ac', ['any', 'ac', 'non_ac'], 'any'),
    seatClass: read('seat_class', ['any', 'seater', 'sleeper'], 'any'),
    tracking: flag('tracking'),
    isNew: flag('is_new'),
    priceMin: params.get('price_min') || '',
    priceMax: params.get('price_max') || '',
    departureWindow: read('departure_window', ['any', 'night', 'morning', 'afternoon', 'evening'], 'any'),
    sort: read('sort', sortOptions.map((option) => option.value), 'recommended'),
  }
}

// How many filters are set, so the button on a phone can say "2 filters".
export function countActiveFilters(filters) {
  let count = 0
  if (filters.ac && filters.ac !== 'any') count += 1
  if (filters.seatClass && filters.seatClass !== 'any') count += 1
  if (filters.tracking) count += 1
  if (filters.isNew) count += 1
  if (String(filters.priceMin).trim()) count += 1
  if (String(filters.priceMax).trim()) count += 1
  if (filters.departureWindow && filters.departureWindow !== 'any') count += 1
  if (filters.sort && filters.sort !== 'recommended') count += 1
  return count
}
