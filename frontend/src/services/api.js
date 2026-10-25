import mockTrip from './mockTrip.js'
import {
  mockFlightResults,
  mockHotelResults,
  mockModifyTrip,
  mockTransportResults,
  mockTripMap,
} from './mockActions.js'
import { filterResults, sortResults } from '../utils/resultFilters.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// When true, functions return sample data instead of calling the backend.
export const isMockMode = import.meta.env.VITE_USE_MOCK === 'true'

// How long to wait for the backend before giving up (itinerary generation can be slow).
const TIMEOUT_MS = 60000

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function request(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      ...options,
    })
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('The server took too long to respond. Try again.')
    }
    throw new Error('Could not reach the server. Check that the backend is running.')
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    // The contract says errors look like { "error": { "code": "...", "message": "..." } }
    let message = `The server returned status ${response.status}. Try again in a moment.`
    try {
      const body = await response.json()
      if (body?.error?.message) message = body.error.message
    } catch {
      // Keep the default message when the body is not JSON.
    }
    throw new Error(message)
  }

  try {
    return await response.json()
  } catch {
    throw new Error('The server sent a response we could not read. Try again.')
  }
}

// Stops a broken response from crashing the pages that display a trip.
function assertTrip(trip) {
  const valid =
    trip &&
    (typeof trip.trip_id === 'string' || typeof trip.trip_id === 'number') &&
    typeof trip.destination === 'string' &&
    Array.isArray(trip.itinerary) &&
    trip.itinerary.every((day) => day && Array.isArray(day.activities))

  if (!valid) {
    throw new Error('The server sent a plan we could not read. Try again.')
  }
  return trip
}

// POST /api/trips
export async function createTrip(tripRequest) {
  if (isMockMode) {
    await wait(800)
    // Sample data, but it uses some values typed in the form so the budget card and the
    // booking options can be tested: budget, travellers, starting place, and travel date.
    const budget = Number(tripRequest?.budget)
    const people = Number(tripRequest?.people)
    return {
      ...mockTrip,
      budget: budget > 0 ? budget : mockTrip.budget,
      people: Number.isInteger(people) && people > 0 ? people : mockTrip.people,
      origin: tripRequest?.origin || null,
      travel_date: tripRequest?.travel_date || null,
    }
  }
  const trip = await request('/api/trips', {
    method: 'POST',
    body: JSON.stringify(tripRequest),
  })
  return assertTrip(trip)
}

// GET /api/trips/{trip_id}
export async function getTrip(tripId) {
  if (isMockMode) {
    await wait(500)
    return mockTrip
  }
  const trip = await request(`/api/trips/${encodeURIComponent(tripId)}`)
  return assertTrip(trip)
}

// POST /api/trips/{trip_id}/modify
// Returns { reply, trip }, where trip is the PROPOSED plan. The page lets the user
// review it before it replaces the current plan.
export async function modifyTrip(tripId, message, currentTrip, history = []) {
  if (isMockMode) {
    await wait(700)
    return mockModifyTrip(currentTrip)
  }
  const data = await request(`/api/trips/${encodeURIComponent(tripId)}/modify`, {
    method: 'POST',
    body: JSON.stringify({ message, current_trip: currentTrip, history }),
  })
  return {
    reply: typeof data?.reply === 'string' ? data.reply : '',
    trip: assertTrip(data?.trip),
  }
}

// Streams the assistant's reply tokens as they are generated, then returns { reply, trip }.
export async function modifyTripStream(
  tripId,
  message,
  currentTrip,
  history = [],
  onToken,
  onDone,
  onError,
) {
  if (isMockMode) {
    try {
      const result = mockModifyTrip(currentTrip)
      const words = result.reply.match(/\S+|\s+/g) || [result.reply]
      for (const word of words) {
        onToken?.(word)
        await wait(20)
      }
      onDone?.(result)
      return result
    } catch (err) {
      onError?.(err)
      throw err
    }
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const response = await fetch(
      `${API_URL}/api/trips/${encodeURIComponent(tripId)}/modify/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, current_trip: currentTrip, history }),
        signal: controller.signal,
      },
    )

    if (!response.ok) {
      let errMsg = `The server returned status ${response.status}.`
      try {
        const body = await response.json()
        if (body?.error?.message) errMsg = body.error.message
      } catch {
        // Keep default error text
      }
      throw new Error(errMsg)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let finalResult = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop()

      for (const block of lines) {
        if (!block.trim()) continue
        const eventMatch = block.match(/^event:\s*(\w+)/m)
        const dataMatch = block.match(/^data:\s*(.*)$/m)
        const eventType = eventMatch ? eventMatch[1] : 'token'
        const dataStr = dataMatch ? dataMatch[1] : ''

        if (eventType === 'token' && dataStr) {
          try {
            const parsed = JSON.parse(dataStr)
            if (parsed.delta) onToken?.(parsed.delta)
          } catch {
            onToken?.(dataStr)
          }
        } else if (eventType === 'done' && dataStr) {
          const parsed = JSON.parse(dataStr)
          finalResult = {
            reply: typeof parsed?.reply === 'string' ? parsed.reply : '',
            trip: assertTrip(parsed?.trip),
          }
          onDone?.(finalResult)
        } else if (eventType === 'error' && dataStr) {
          const parsed = JSON.parse(dataStr)
          throw new Error(parsed?.message || 'Modification failed.')
        }
      }
    }

    if (!finalResult) {
      const fallback = await modifyTrip(tripId, message, currentTrip, history)
      onDone?.(fallback)
      return fallback
    }

    return finalResult
  } catch (caught) {
    if (caught.name === 'AbortError') {
      const timeoutError = new Error('The server took too long to respond. Try again.')
      onError?.(timeoutError)
      throw timeoutError
    }
    onError?.(caught)
    throw caught
  } finally {
    clearTimeout(timer)
  }
}

function assertResults(data) {
  if (!data || !Array.isArray(data.results)) {
    throw new Error('The server sent results we could not read. Try again.')
  }
  return {
    is_mock: Boolean(data.is_mock),
    results: data.results.filter((item) => item && typeof item === 'object'),
  }
}

// Applies the filters to the sample data, so the sample mode behaves the
// same way the real backend does. The backend applies the same rules
// (see `backend/app/services/filters.py`).
function mockResults(data, params) {
  const filters = params?.filters || {}
  const concession = params?.concession || null

  const results = filterResults(data.results, {
    ac: filters.ac || 'any',
    seatClass: filters.seat_class || 'any',
    tracking: Boolean(filters.tracking),
    isNew: Boolean(filters.is_new),
    priceMin: filters.price_min ?? '',
    priceMax: filters.price_max ?? '',
    departureWindow: filters.departure_window || 'any',
  }, concession)

  return { ...data, results: sortResults(results, filters.sort || 'recommended') }
}

// POST /api/flights/search
export async function searchFlights(params) {
  if (isMockMode) {
    await wait(700)
    return mockResults(mockFlightResults(), params)
  }
  return assertResults(
    await request('/api/flights/search', { method: 'POST', body: JSON.stringify(params) }),
  )
}

// POST /api/hotels/search
export async function searchHotels(params) {
  if (isMockMode) {
    await wait(700)
    return mockResults(mockHotelResults(), params)
  }
  return assertResults(
    await request('/api/hotels/search', { method: 'POST', body: JSON.stringify(params) }),
  )
}

// POST /api/transport/search (buses and trains)
// params: { mode: 'bus' | 'train', origin, destination, date, passengers }
export async function searchTransport(params) {
  if (isMockMode) {
    await wait(700)
    return mockResults(mockTransportResults(params.mode), params)
  }
  return assertResults(
    await request('/api/transport/search', { method: 'POST', body: JSON.stringify(params) }),
  )
}

// GET /api/trips/{trip_id}/map
// Returns the stops and the route of every day of the trip.
export async function getTripMap(tripId) {
  if (isMockMode) {
    await wait(600)
    return mockTripMap()
  }
  const data = await request(`/api/trips/${encodeURIComponent(tripId)}/map`)
  if (!data || !Array.isArray(data.days)) {
    throw new Error('The server sent a map we could not read. Try again.')
  }
  return data
}

// GET /api/maps/geocode
// Looks up one place name. Returns { place, error } when it cannot be found.
export async function geocodePlace(place) {
  if (isMockMode) {
    await wait(300)
    return { place, error: 'The map service is not available in sample mode.' }
  }
  return request(`/api/maps/geocode?place=${encodeURIComponent(place)}`)
}
