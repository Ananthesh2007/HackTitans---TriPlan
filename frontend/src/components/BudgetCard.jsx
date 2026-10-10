import { formatMoney } from '../utils/format.js'

// Cost categories in the order they are shown. Rows are only shown when the
// backend sends a number for that category.
const ROWS = [
  { key: 'flights', label: 'Flights' },
  { key: 'accommodation', label: 'Accommodation' },
  { key: 'food', label: 'Food' },
  { key: 'activities', label: 'Activities' },
  { key: 'local_transport', label: 'Local transport' },
]

const isAmount = (value) => typeof value === 'number' && Number.isFinite(value)

// Shows the estimated cost breakdown and compares the total with the user's budget.
export default function BudgetCard({ budget, costs, currency }) {
  const rows = costs ? ROWS.filter(({ key }) => isAmount(costs[key])) : []

  if (!costs || (rows.length === 0 && !isAmount(costs.total))) {
    return (
      <section aria-labelledby="budget-heading" className="max-w-xl border border-line bg-white p-5">
        <h2 id="budget-heading" className="text-xl font-semibold">
          Estimated budget
        </h2>
        <p className="mt-2 text-muted">A cost estimate is not available for this plan.</p>
      </section>
    )
  }

  // Prefer the total from the backend. Fall back to adding up the rows shown.
  const total = isAmount(costs.total)
    ? costs.total
    : rows.reduce((sum, { key }) => sum + costs[key], 0)

  const hasBudget = isAmount(budget) && budget > 0
  const difference = hasBudget ? total - budget : 0
  const isOver = hasBudget && difference > 0
  const barShare = hasBudget ? Math.min(total / budget, 1) * 100 : 0

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
    <section aria-labelledby="budget-heading" className="max-w-xl border border-line bg-white p-5">
      <h2 id="budget-heading" className="text-xl font-semibold">
        Estimated budget
      </h2>

      <dl className="mt-4 divide-y divide-line">
        {rows.map(({ key, label }) => (
          <div key={key} className="flex justify-between gap-4 py-2">
            <dt className="text-muted">{label}</dt>
            <dd>{formatMoney(costs[key], currency)}</dd>
          </div>
        ))}
        <div className="flex justify-between gap-4 py-2 font-semibold">
          <dt>Estimated total</dt>
          <dd>{formatMoney(total, currency)}</dd>
        </div>
      </dl>

      {hasBudget && (
        <div className="mt-4">
          <p className="text-sm text-muted">Your budget: {formatMoney(budget, currency)}</p>
          <div className="mt-2 h-2 w-full bg-line" aria-hidden="true">
            <div
              className={`h-2 ${isOver ? 'bg-red-700' : 'bg-brand'}`}
              style={{ width: `${barShare}%` }}
            />
          </div>
          <p role="status" className={`mt-3 font-medium ${isOver ? 'text-red-700' : 'text-brand'}`}>
            {statusText}
          </p>
          {isOver && (
            <p className="mt-1 text-sm text-muted">
              To bring the cost down, shorten the trip, choose cheaper activities, or raise your
              budget.
            </p>
          )}
        </div>
      )}

      <p className="mt-4 text-sm text-muted">Estimates only. Actual prices may differ.</p>
    </section>
  )
}