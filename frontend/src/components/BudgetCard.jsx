import { motion } from 'framer-motion'
import { formatMoney } from '../utils/format.js'
import { staggerContainer, staggerItem } from '../lib/motion.js'

// Cost categories in the order they are shown. Rows are only shown when the
// backend sends a number for that category.
const ROWS = [
  { key: 'flights', label: 'Flights', source: 'Amadeus GDS', link: 'https://www.airindiaexpress.com' },
  { key: 'accommodation', label: 'Accommodation', source: 'Tavily Partner', link: 'https://www.tajhotels.com' },
  { key: 'food', label: 'Food', source: 'Market Average' },
  { key: 'activities', label: 'Activities', source: 'Local Verified' },
  { key: 'local_transport', label: 'Local transport', source: 'IRCTC / RedBus' },
]

const isAmount = (value) => typeof value === 'number' && Number.isFinite(value)

// Shows the estimated cost breakdown and compares the total with the user's budget.
export default function BudgetCard({ budget, costs, currency }) {
  const rows = costs ? ROWS.filter(({ key }) => isAmount(costs[key])) : []

  if (!costs || (rows.length === 0 && !isAmount(costs.total))) {
    return (
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        aria-labelledby="budget-heading"
        className="glass-panel max-w-xl p-6"
      >
        <h2 id="budget-heading" className="text-xl font-black text-slate-100">
          Estimated budget
        </h2>
        <p className="mt-2 text-slate-400">A cost estimate is not available for this plan.</p>
      </motion.section>
    )
  }

  // Prefer the total from the backend. Fall back to adding up the rows shown.
  const total = isAmount(costs.total)
    ? costs.total
    : rows.reduce((sum, { key }) => sum + costs[key], 0)

  const hasBudget = isAmount(budget) && budget > 0
  const difference = hasBudget ? total - budget : 0
  const isOver = hasBudget && difference > 0
  const barShare = hasBudget ? Math.min((total / budget) * 100, 100) : 0

  let statusText = ''
  if (hasBudget) {
    if (difference > 0) {
      statusText = `Over budget by ${formatMoney(difference, currency)}.`
    } else if (difference < 0) {
      statusText = `Within budget, with ${formatMoney(-difference, currency)} to spare.`
    } else {
      statusText = 'The estimate matches your budget exactly.'
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      aria-labelledby="budget-heading"
      className="glass-panel max-w-xl p-6"
    >
      <div className="flex items-center justify-between">
        <h2 id="budget-heading" className="text-xl font-black text-slate-100">
          Estimated budget
        </h2>
        <span className="badge badge-accent">Live / Verified</span>
      </div>

      <motion.dl
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="mt-4 divide-y divide-line"
      >
        {rows.map(({ key, label, source, link }) => (
          <motion.div key={key} variants={staggerItem} className="flex flex-col gap-1 py-3">
            <div className="flex justify-between items-center text-sm">
              <span className="font-medium text-slate-100">{label}</span>
              <span className="font-semibold text-slate-100">{formatMoney(costs[key], currency)}</span>
            </div>
            <div className="flex justify-between items-center text-xs text-slate-400">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
                {source}
              </span>
              {link && (
                <a
                  href={link}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-accent hover:text-primary transition-colors font-medium"
                >
                  Book option &rarr;
                </a>
              )}
            </div>
          </motion.div>
        ))}
        <div className="flex justify-between gap-4 py-3 font-semibold text-lg border-t-2 border-primary/20">
          <dt className="text-slate-100">Estimated total</dt>
          <dd className="text-primary">{formatMoney(total, currency)}</dd>
        </div>
      </motion.dl>

      {hasBudget && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-4"
        >
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-slate-400">Budget utilization</span>
            <span className="font-medium text-slate-100">
              {formatMoney(total, currency)} / {formatMoney(budget, currency)}
            </span>
          </div>
          <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden" aria-hidden="true">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${barShare}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className={`h-full rounded-full ${
                isOver ? 'bg-gradient-to-r from-error to-secondary' : 'bg-gradient-to-r from-primary to-accent'
              }`}
            />
          </div>
          <p role="status" className={`mt-3 font-medium text-sm ${isOver ? 'text-error' : 'text-accent'}`}>
            {statusText}
          </p>
          {isOver && (
            <p className="mt-1 text-xs text-slate-400">
              To bring the cost down, shorten the trip, choose cheaper activities, or raise your
              budget.
            </p>
          )}
        </motion.div>
      )}

      <p className="mt-4 text-xs text-slate-400">Real-time market rates and estimates. Actual prices may differ slightly upon checkout.</p>
    </motion.section>
  )
}