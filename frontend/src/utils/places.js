// A small list of places, so the search boxes can suggest a name before the
// user has finished typing it.
//
// The list is a starting point, not the whole world. When a name is not in
// it, the search page asks the backend to look the place up
// (`GET /api/maps/geocode`), so anything the maps provider knows can be
// used as well.

// The name, state, and kind of each place shown in the dropdown.
const PLACES = [
  // Airports
  { name: 'Kempegowda International Airport', state: 'Karnataka', type: 'airport', icon: 'airport' },
  { name: 'Chhatrapati Shivaji Maharaj International Airport', state: 'Maharashtra', type: 'airport', icon: 'airport' },
  { name: 'Indira Gandhi International Airport', state: 'Delhi', type: 'airport', icon: 'airport' },
  { name: 'Rajiv Gandhi International Airport', state: 'Telangana', type: 'airport', icon: 'airport' },
  { name: 'Chennai International Airport', state: 'Tamil Nadu', type: 'airport', icon: 'airport' },
  { name: 'Netaji Subhas Chandra Bose International Airport', state: 'West Bengal', type: 'airport', icon: 'airport' },
  { name: 'Sardar Vallabhbhai Patel International Airport', state: 'Gujarat', type: 'airport', icon: 'airport' },
  { name: 'Cochin International Airport', state: 'Kerala', type: 'airport', icon: 'airport' },
  { name: 'Lokpriya Gopinath Bordoloi International Airport', state: 'Assam', type: 'airport', icon: 'airport' },
  { name: 'Jaipur International Airport', state: 'Rajasthan', type: 'airport', icon: 'airport' },
  { name: 'Lucknow International Airport', state: 'Uttar Pradesh', type: 'airport', icon: 'airport' },
  { name: 'Bengaluru International Airport', state: 'Karnataka', type: 'airport', icon: 'airport' },
  { name: 'Amritsar International Airport', state: 'Punjab', type: 'airport', icon: 'airport' },
  { name: 'Goa Dabolim Airport', state: 'Goa', type: 'airport', icon: 'airport' },
  { name: 'Chandigarh International Airport', state: 'Punjab', type: 'airport', icon: 'airport' },

  // Cities
  { name: 'Mumbai', state: 'Maharashtra', type: 'city' },
  { name: 'Delhi', state: 'Delhi', type: 'city' },
  { name: 'Bengaluru', state: 'Karnataka', type: 'city' },
  { name: 'Hyderabad', state: 'Telangana', type: 'city' },
  { name: 'Chennai', state: 'Tamil Nadu', type: 'city' },
  { name: 'Kolkata', state: 'West Bengal', type: 'city' },
  { name: 'Pune', state: 'Maharashtra', type: 'city' },
  { name: 'Ahmedabad', state: 'Gujarat', type: 'city' },
  { name: 'Jaipur', state: 'Rajasthan', type: 'city' },
  { name: 'Lucknow', state: 'Uttar Pradesh', type: 'city' },
  { name: 'Kochi', state: 'Kerala', type: 'city' },
  { name: 'Guwahati', state: 'Assam', type: 'city' },
  { name: 'Chandigarh', state: 'Punjab', type: 'city' },
  { name: 'Indore', state: 'Madhya Pradesh', type: 'city' },
  { name: 'Nagpur', state: 'Maharashtra', type: 'city' },
  { name: 'Bhopal', state: 'Madhya Pradesh', type: 'city' },
  { name: 'Patna', state: 'Bihar', type: 'city' },
  { name: 'Bhubaneswar', state: 'Odisha', type: 'city' },
  { name: 'Varanasi', state: 'Uttar Pradesh', type: 'city' },
  { name: 'Amritsar', state: 'Punjab', type: 'city' },
  { name: 'Ludhiana', state: 'Punjab', type: 'city' },
  { name: 'Dehradun', state: 'Uttarakhand', type: 'city' },
  { name: 'Coimbatore', state: 'Tamil Nadu', type: 'city' },
  { name: 'Madurai', state: 'Tamil Nadu', type: 'city' },
  { name: 'Vadodara', state: 'Gujarat', type: 'city' },
  { name: 'Nashik', state: 'Maharashtra', type: 'city' },
  { name: 'Surat', state: 'Gujarat', type: 'city' },
  { name: 'Ranchi', state: 'Jharkhand', type: 'city' },
  { name: 'Raipur', state: 'Chhattisgarh', type: 'city' },
  { name: 'Thiruvananthapuram', state: 'Kerala', type: 'city' },
  { name: 'Mysuru', state: 'Karnataka', type: 'city' },
  { name: 'Mangaluru', state: 'Karnataka', type: 'city' },
  { name: 'Hubballi', state: 'Karnataka', type: 'city' },
  { name: 'Solapur', state: 'Maharashtra', type: 'city' },
  { name: 'Kolhapur', state: 'Maharashtra', type: 'city' },
  { name: 'Udaipur', state: 'Rajasthan', type: 'city' },
  { name: 'Jodhpur', state: 'Rajasthan', type: 'city' },
  { name: 'Jamshedpur', state: 'Jharkhand', type: 'city' },
  { name: 'Siliguri', state: 'West Bengal', type: 'city' },
  { name: 'Thiruvananthapuram Airport', state: 'Kerala', type: 'airport' },
  { name: 'Dharwad', state: 'Karnataka', type: 'city' },
  { name: 'Udupi', state: 'Karnataka', type: 'city' },
  { name: 'Hassan', state: 'Karnataka', type: 'city' },
  { name: 'Shimoga', state: 'Karnataka', type: 'city' },
  { name: 'Belgaum', state: 'Karnataka', type: 'city' },
  { name: 'Kollam', state: 'Kerala', type: 'city' },
  { name: 'Kozhikode', state: 'Kerala', type: 'city' },
  { name: 'Thrissur', state: 'Kerala', type: 'city' },
  { name: 'Gwalior', state: 'Madhya Pradesh', type: 'city' },
  { name: 'Jabalpur', state: 'Madhya Pradesh', type: 'city' },
  { name: 'Ujjain', state: 'Madhya Pradesh', type: 'city' },
  { name: 'Aurangabad', state: 'Maharashtra', type: 'city' },
  { name: 'Navi Mumbai', state: 'Maharashtra', type: 'city' },
  { name: 'Thane', state: 'Maharashtra', type: 'city' },
  { name: 'Panaji', state: 'Goa', type: 'city' },
  { name: 'Margao', state: 'Goa', type: 'city' },
  { name: 'Varanasi Airport', state: 'Uttar Pradesh', type: 'airport' },
  { name: 'Allahabad', state: 'Uttar Pradesh', type: 'city' },
  { name: 'Bareilly', state: 'Uttar Pradesh', type: 'city' },
  { name: 'Agra', state: 'Uttar Pradesh', type: 'city' },
  { name: 'Kanpur', state: 'Uttar Pradesh', type: 'city' },
  { name: 'Nagpur Airport', state: 'Maharashtra', type: 'airport' },
  { name: 'Visakhapatnam', state: 'Andhra Pradesh', type: 'city' },
  { name: 'Vijayawada', state: 'Andhra Pradesh', type: 'city' },
  { name: 'Tirupati', state: 'Andhra Pradesh', type: 'city' },
  { name: 'Coorg', state: 'Karnataka', type: 'city' },
  { name: 'Chikmagalur', state: 'Karnataka', type: 'city' },
  { name: 'Bandipur', state: 'Karnataka', type: 'city' },
  { name: 'Ooty', state: 'Tamil Nadu', type: 'city' },
  { name: 'Kodaikanal', state: 'Tamil Nadu', type: 'city' },
  { name: 'Wayanad', state: 'Kerala', type: 'city' },
  { name: 'Munnar', state: 'Kerala', type: 'city' },
  { name: 'Alappuzha', state: 'Kerala', type: 'city' },
  { name: 'Puducherry', state: 'Puducherry', type: 'city' },
  { name: 'Port Blair', state: 'Andaman and Nicobar Islands', type: 'city' },
  { name: 'Shimla', state: 'Himachal Pradesh', type: 'city' },
  { name: 'Manali', state: 'Himachal Pradesh', type: 'city' },
  { name: 'Srinagar', state: 'Jammu and Kashmir', type: 'city' },
  { name: 'Jaisalmer', state: 'Rajasthan', type: 'city' },
  { name: 'Pushkar', state: 'Rajasthan', type: 'city' },
  { name: 'Rishikesh', state: 'Uttarakhand', type: 'city' },
  { name: 'Haridwar', state: 'Uttarakhand', type: 'city' },
  { name: 'Digha', state: 'West Bengal', type: 'city' },
  { name: 'Puri', state: 'Odisha', type: 'city' },
  { name: 'Puri Beach', state: 'Odisha', type: 'city' },
  { name: 'Gopalpur', state: 'Odisha', type: 'city' },
]

// The places, ready to be searched.
export const PLACE_SUGGESTIONS = PLACES.map((place) => ({
  ...place,
  label: place.name,
  secondary: place.state,
}))

// The places that match what the user has typed so far.
// A place matches when its name starts with the text, or when the text
// appears anywhere in the name.
export function searchPlaces(query, limit = 8) {
  const text = String(query || '').trim().toLowerCase()
  if (text.length < 2) return []

  const starts = []
  const contains = []

  for (const place of PLACE_SUGGESTIONS) {
    const name = place.name.toLowerCase()
    const state = place.state.toLowerCase()

    if (name.startsWith(text)) starts.push(place)
    else if (name.includes(text) || state.includes(text)) contains.push(place)

    if (starts.length >= limit) break
  }

  return [...starts, ...contains].slice(0, limit)
}

// The popular cities to show when the box is first opened. They are the
// most-visited destinations, so they are useful without any typing.
export function searchPopular(limit = 6) {
  return PLACE_SUGGESTIONS.filter((place) => place.type === 'city').slice(0, limit)
}
