import { motion } from 'framer-motion'
import { formatMoney } from '../utils/format.js'
import { staggerContainer, staggerItem } from '../lib/motion.js'

// Shows one day of the itinerary: title, activities, times, places, and estimated costs.
export default function ItineraryCard({ day, currency, people = 1 }) {
  const dayTotal = day.activities.reduce((sum, activity) => sum + activity.estimated_cost, 0)
  // The budget card shows group totals, so this card shows them too. Without
  // this the two panels on the dashboard disagree about the same costs.
  const groupTotal = dayTotal * people

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-panel p-6"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-xl font-black text-slate-100">
          Day {day.day}: {day.title}
        </h2>
        <p className="text-sm text-slate-400">
          Estimated activities cost: {formatMoney(groupTotal, currency)}
          {people > 1 ? ` (${formatMoney(dayTotal, currency)} per person)` : ''}
        </p>
      </header>

      <motion.ul
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="mt-4 divide-y divide-line scrollbar-custom"
      >
        {day.activities.map((activity, index) => (
          <motion.li
            key={`${activity.time}-${activity.name}`}
            variants={staggerItem}
            className="grid grid-cols-[4rem_1fr] gap-x-4 py-3 sm:grid-cols-[4rem_1fr_auto] hover:bg-slate-800/20 transition-colors rounded-md px-2 -mx-2"
          >
            <span className="text-accent font-semibold">{activity.time}</span>
            <div>
              <p className="font-medium text-slate-100">{activity.name}</p>
              <p className="text-sm text-slate-400">{activity.location}</p>
            </div>
            <p className="col-start-2 mt-1 text-sm sm:col-start-3 sm:mt-0 sm:text-base font-semibold text-slate-200">
              {formatMoney(activity.estimated_cost * people, currency)}
            </p>
          </motion.li>
        ))}
      </motion.ul>
    </motion.article>
  )
}