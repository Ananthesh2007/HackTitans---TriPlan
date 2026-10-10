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

export function mockTransportResults(mode) {
  if (mode === 'train') {
    return {
      is_mock: true,
      results: [
        { id: 'sample-train-1', operator: 'Sample Express 1', vehicle_type: 'Sleeper class', departure_time: '20:10', arrival_time: '06:00', duration: '9h 50m', price: 480, currency: 'INR', booking_url: null },
        { id: 'sample-train-2', operator: 'Sample Express 2', vehicle_type: 'AC 3 tier', departure_time: '22:40', arrival_time: '07:20', duration: '8h 40m', price: 1250, currency: 'INR', booking_url: null },
        { id: 'sample-train-3', operator: 'Sample Passenger 3', vehicle_type: 'Second sitting', departure_time: '05:30', arrival_time: '15:10', duration: '9h 40m', price: 190, currency: 'INR', booking_url: null },
      ],
    }
  }
  return {
    is_mock: true,
    results: [
      { id: 'sample-bus-1', operator: 'Sample Bus Operator A', vehicle_type: 'AC sleeper', departure_time: '21:30', arrival_time: '05:15', duration: '7h 45m', price: 900, currency: 'INR', booking_url: null },
      { id: 'sample-bus-2', operator: 'Sample Bus Operator B', vehicle_type: 'Non-AC seater', departure_time: '22:00', arrival_time: '06:30', duration: '8h 30m', price: 550, currency: 'INR', booking_url: null },
      { id: 'sample-bus-3', operator: 'Sample Bus Operator C', vehicle_type: 'AC seater', departure_time: '23:15', arrival_time: '06:45', duration: '7h 30m', price: 750, currency: 'INR', booking_url: null },
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