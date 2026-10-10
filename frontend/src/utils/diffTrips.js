const isAmount = (value) => typeof value === 'number' && Number.isFinite(value)

// Lists every activity with a key made of its day, name, and how many times
// that name already appeared on the day (so two "Lunch" entries do not collide).
function activityMap(trip) {
  const map = new Map()
  for (const day of trip.itinerary) {
    const seen = new Map()
    for (const activity of day.activities) {
      const count = (seen.get(activity.name) ?? 0) + 1
      seen.set(activity.name, count)
      map.set(`${day.day}|${activity.name}|${count}`, {
        day: day.day,
        name: activity.name,
        time: activity.time,
        cost: Number(activity.estimated_cost) || 0,
      })
    }
  }
  return map
}

// Compares the current trip with a proposed one and describes what would change.
export function diffTrips(current, proposed) {
  const before = activityMap(current)
  const after = activityMap(proposed)

  const added = []
  const removed = []
  const changed = []

  for (const [key, item] of after) {
    const old = before.get(key)
    if (!old) {
      added.push(item)
    } else if (old.cost !== item.cost || old.time !== item.time) {
      changed.push({ ...item, oldCost: old.cost, oldTime: old.time })
    }
  }
  for (const [key, item] of before) {
    if (!after.has(key)) removed.push(item)
  }

  const totalBefore = isAmount(current.estimated_costs?.total) ? current.estimated_costs.total : null
  const totalAfter = isAmount(proposed.estimated_costs?.total) ? proposed.estimated_costs.total : null

  return {
    added,
    removed,
    changed,
    totalBefore,
    totalAfter,
    hasChanges:
      added.length > 0 || removed.length > 0 || changed.length > 0 || totalBefore !== totalAfter,
  }
}