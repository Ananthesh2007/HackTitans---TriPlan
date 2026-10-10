// Sample data for development only. Never show this to users as a real plan.
// All costs are made-up placeholders in INR for the whole group.
const mockTrip = {
  trip_id: 'mock-001',
  is_mock: true,
  is_estimate: true,
  destination: 'Coorg',
  days: 3,
  people: 2,
  budget: 15000,
  currency: 'INR',
  estimated_costs: {
    accommodation: 6000,
    food: 3000,
    activities: 2600,
    local_transport: 2000,
    total: 13600,
  },
  itinerary: [
    {
      day: 1,
      title: 'Viewpoints and waterfalls',
      activities: [
        { time: '09:00', name: "Raja's Seat", location: 'Madikeri', estimated_cost: 100 },
        { time: '14:00', name: 'Abbey Falls', location: 'Madikeri', estimated_cost: 200 },
      ],
    },
    {
      day: 2,
      title: 'Elephants and plantations',
      activities: [
        { time: '09:00', name: 'Dubare Elephant Camp', location: 'Kushalnagar', estimated_cost: 1200 },
        { time: '14:00', name: 'Plantation walk', location: 'Madikeri', estimated_cost: 800 },
      ],
    },
    {
      day: 3,
      title: 'Island park and monastery',
      activities: [
        { time: '09:00', name: 'Nisargadhama', location: 'Kushalnagar', estimated_cost: 300 },
        { time: '13:00', name: 'Namdroling Monastery', location: 'Bylakuppe', estimated_cost: 0 },
      ],
    },
  ],
}

export default mockTrip