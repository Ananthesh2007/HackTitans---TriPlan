import { formatMoney } from '../utils/format.js'

// Shows one day of the itinerary: title, activities, times, places, and estimated costs.
export default function ItineraryCard({ day, currency, people = 1 }) {
  const dayTotal = day.activities.reduce((sum, activity) => sum + activity.estimated_cost, 0)
  // The budget card shows group totals, so this card shows them too. Without
  // this the two panels on the dashboard disagree about the same costs.
  const groupTotal = dayTotal * people

  return (
    <article className="border-t border-line pt-4">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-xl font-semibold">
          Day {day.day}: {day.title}
        </h2>
        <p className="text-sm text-muted">
          Estimated activities cost: {formatMoney(groupTotal, currency)}
          {people > 1 ? ` (${formatMoney(dayTotal, currency)} per person)` : ''}
        </p>
      </header>

      <ul className="mt-4 divide-y divide-line">
        {day.activities.map((activity) => (
          <li
            key={`${activity.time}-${activity.name}`}
            className="grid grid-cols-[4rem_1fr] gap-x-4 py-3 sm:grid-cols-[4rem_1fr_auto]"
          >
            <span className="text-muted">{activity.time}</span>
            <div>
              <p className="font-medium">{activity.name}</p>
              <p className="text-sm text-muted">{activity.location}</p>
            </div>
            <p className="col-start-2 mt-1 text-sm sm:col-start-3 sm:mt-0 sm:text-base">
              {formatMoney(activity.estimated_cost * people, currency)}
            </p>
          </li>
        ))}
      </ul>
    </article>
  )
}