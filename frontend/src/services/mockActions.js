// Sample data for development only. None of this is real. The pages label it as sample data.

export function mockFlightResults() {
  return {
    is_mock: true,
    results: [
      { id: 'sample-flight-1', airline: 'Sample Airline A', departure_time: '06:30', arrival_time: '08:45', duration: '2h 15m', stops: 0, price: 4800, currency: 'INR', booking_url: null },
      { id: 'sample-flight-2', airline: 'Sample Airline B', departure_time: '11:10', arrival_time: '14:50', duration: '3h 40m', stops: 1, price: 3900, currency: 'INR', booking_url: null },
      { id: 'sample-flight-3', airline: 'Sample Airline C', departure_time: '18:20', arrival_time: '20:35', duration: '2h 15m', stops: 0, price: 5600, currency: 'INR', booking_url: null },
    ],
  }
}

export function mockHotelResults() {
  return {
    is_mock: true,
    results: [
      { id: 'sample-hotel-1', name: 'Sample Hotel A', area: 'City centre', price_per_night: 2200, currency: 'INR', booking_url: null },
      { id: 'sample-hotel-2', name: 'Sample Hotel B', area: 'Near the station', price_per_night: 1500, currency: 'INR', booking_url: null },
      { id: 'sample-hotel-3', name: 'Sample Hotel C', area: 'Quiet outskirts', price_per_night: 3400, currency: 'INR', booking_url: null },
    ],
  }
}

// Pretends to be the assistant: removes the most expensive activity and lowers the totals.
// This lets the review and budget screens be tested without a backend.
export function mockModifyTrip(currentTrip) {
  const trip = structuredClone(currentTrip)

  let target = null
  trip.itinerary.forEach((day, dayIndex) => {
    day.activities.forEach((activity, activityIndex) => {
      const cost = Number(activity.estimated_cost) || 0
      if (cost > 0 && (!target || cost > target.cost)) {
        target = { dayIndex, activityIndex, cost, name: activity.name, day: day.day }
      }
    })
  })

  if (!target) {
    return {
      reply: 'Sample reply: there was nothing to remove. This is not a real AI response.',
      trip,
    }
  }

  trip.itinerary[target.dayIndex].activities.splice(target.activityIndex, 1)
  const costs = trip.estimated_costs
  if (costs) {
    if (typeof costs.activities === 'number') costs.activities -= target.cost
    if (typeof costs.total === 'number') costs.total -= target.cost
  }

  return {
    reply: `Sample reply: I removed "${target.name}" from day ${target.day} to lower the cost. This is a development sample, not a real AI response.`,
    trip,
  }
}