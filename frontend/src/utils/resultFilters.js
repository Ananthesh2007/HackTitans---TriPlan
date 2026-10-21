// Filters and sorts the results on a search page.
//
// The backend filters and sorts too (see `backend/app/services/filters.py`).
// Doing it here as well means the page behaves the same when it runs on the
// built-in sample data, and that changing a filter updates the list straight
// away, without another search.

// The time windows, in minutes after midnight.
const WINDOWS = {
  night: [0, 360],
  morning: [360, 720],
  afternoon: [720, 1080],
  evening: [1080, 1440],
}

// Minutes after midnight for an "HH:MM" string, or null.
export function timeMinutes(value) {
  if (typeof value !== 'string') return null
  const match = value.trim().match(/^(\d{1,2}):(\d{2})/)
  if (!match) return null
  const hours = Number(match[1])
  const minutes = Number(match[2])
  if (hours > 23 || minutes > 59) return null
  return hours * 60 + minutes
}

// The price of a result, whichever field holds it.
export function priceOf(result) {
  for (const key of ['price', 'price_per_night']) {
    const value = result?.[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
  }
  return null
}

// The length of a trip, from a "9h 50m" style string.
export function durationMinutes(result) {
  const duration = result?.duration
  if (typeof duration !== 'string') return null
  const hours = duration.match(/(\d+)\s*h/)
  const minutes = duration.match(/(\d+)\s*m/)
  if (!hours && !minutes) return null
  return (hours ? Number(hours[1]) * 60 : 0) + (minutes ? Number(minutes[1]) : 0)
}

// True when the vehicle type says AC, False for non-AC, null when it does not say.
export function hasAc(result) {
  const type = result?.vehicle_type
  if (typeof type !== 'string') return null
  if (/non[\s\-_]*ac/i.test(type)) return false
  if (/(^|[^a-z])ac($|[^a-z])/i.test(type)) return true
  return null
}

// True when the result can be booked with the chosen concession.
// A result that does not list its concessions is kept, because the provider
// did not say it was excluded.
export function matchesConcession(result, concession) {
  if (!concession) return true
  const offered = result?.concessions
  if (!Array.isArray(offered) || offered.length === 0) return true
  return offered.includes(concession)
}

// True when the price is inside the chosen range.
export function matchesPrice(result, filters) {
  const price = priceOf(result)
  if (price === null) return true
  const min = Number(filters.priceMin)
  const max = Number(filters.priceMax)
  if (Number.isFinite(min) && min > 0 && price < min) return false
  if (Number.isFinite(max) && max > 0 && price > max) return false
  return true
}

// True when the result matches the AC, seat class, tracking and new filters.
export function matchesVehicle(result, filters) {
  if (filters.ac && filters.ac !== 'any') {
    const ac = hasAc(result)
    if (ac !== null && ac !== (filters.ac === 'ac')) return false
  }

  if (filters.seatClass && filters.seatClass !== 'any') {
    const type = result?.vehicle_type
    if (typeof type === 'string' && !type.toLowerCase().includes(filters.seatClass)) {
      return false
    }
  }

  if (filters.tracking && !result?.tracking) return false
  if (filters.isNew && !result?.is_new) return false

  return true
}

// True when the departure (or check-in) time falls in the chosen window.
export function matchesTime(result, filters) {
  const window = filters.departureWindow
  if (!window || window === 'any') return true
  const bounds = WINDOWS[window]
  if (!bounds) return true

  const time = result?.departure_time || result?.check_in_time
  const minutes = timeMinutes(time)
  if (minutes === null) return true

  return minutes >= bounds[0] && minutes < bounds[1]
}

// Keeps only the results that match the filters.
export function filterResults(results, filters, concession) {
  if (!Array.isArray(results)) return []
  return results.filter(
    (result) =>
      matchesConcession(result, concession) &&
      matchesPrice(result, filters) &&
      matchesVehicle(result, filters) &&
      matchesTime(result, filters),
  )
}

// Sorts the results the way the user asked for.
export function sortResults(results, sort) {
  if (!Array.isArray(results)) return []
  if (!sort || sort === 'recommended') return results

  const sorted = [...results]

  if (sort === 'price_asc' || sort === 'price_desc') {
    const sign = sort === 'price_asc' ? 1 : -1
    sorted.sort((first, second) => {
      const a = priceOf(first)
      const b = priceOf(second)
      if (a === null && b === null) return 0
      if (a === null) return 1
      if (b === null) return -1
      return (a - b) * sign
    })
    return sorted
  }

  if (sort === 'departure_asc' || sort === 'departure_desc') {
    const sign = sort === 'departure_asc' ? 1 : -1
    sorted.sort((first, second) => {
      const a = timeMinutes(first?.departure_time)
      const b = timeMinutes(second?.departure_time)
      if (a === null && b === null) return 0
      if (a === null) return 1
      if (b === null) return -1
      return (a - b) * sign
    })
    return sorted
  }

  if (sort === 'duration_asc') {
    sorted.sort((first, second) => {
      const a = durationMinutes(first)
      const b = durationMinutes(second)
      if (a === null && b === null) return 0
      if (a === null) return 1
      if (b === null) return -1
      return a - b
    })
    return sorted
  }

  if (sort === 'name_asc') {
    sorted.sort((first, second) => {
      const a = (first?.name || first?.operator || first?.airline || '').toLowerCase()
      const b = (second?.name || second?.operator || second?.airline || '').toLowerCase()
      return a.localeCompare(b)
    })
  }

  return sorted
}

// Filters and sorts in one step, the way the page shows the results.
export function applyFiltersAndSort(results, filters, concession) {
  return sortResults(filterResults(results, filters, concession), filters.sort)
}
