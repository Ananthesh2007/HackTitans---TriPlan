import mockTrip from './mockTrip.js'

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
    // Sample data, but it uses the budget typed in the form so the budget card can be tested.
    const budget = Number(tripRequest?.budget)
    return { ...mockTrip, budget: budget > 0 ? budget : mockTrip.budget }
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