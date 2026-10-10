import { useState } from 'react'
import { modifyTrip } from '../services/api.js'
import { diffTrips } from '../utils/diffTrips.js'
import { formatMoney } from '../utils/format.js'

const MAX_LENGTH = 500

function ChangeList({ diff, currency }) {
  const hasTotals = diff.totalBefore !== null && diff.totalAfter !== null

  return (
    <div className="mt-3 border border-line bg-white p-4">
      <h3 className="text-lg font-semibold">Proposed changes</h3>
      <ul className="mt-3 space-y-2 text-sm">
        {diff.removed.map((item) => (
          <li key={`r-${item.day}-${item.name}`}>
            Remove: {item.name} (day {item.day}, {formatMoney(item.cost, currency)})
          </li>
        ))}
        {diff.added.map((item) => (
          <li key={`a-${item.day}-${item.name}`}>
            Add: {item.name} (day {item.day}, {formatMoney(item.cost, currency)})
          </li>
        ))}
        {diff.changed.map((item) => (
          <li key={`c-${item.day}-${item.name}`}>
            Change: {item.name} (day {item.day}), cost {formatMoney(item.oldCost, currency)} to{' '}
            {formatMoney(item.cost, currency)}
          </li>
        ))}
      </ul>
      {hasTotals && (
        <p className="mt-3 font-medium">
          Estimated total: {formatMoney(diff.totalBefore, currency)} to{' '}
          {formatMoney(diff.totalAfter, currency)}
        </p>
      )}
    </div>
  )
}

// Lets the user ask for changes. The assistant only proposes a new plan.
// Nothing changes until the user chooses Apply.
export default function ChatAssistant({ trip, onApply }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [proposal, setProposal] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()
    if (isSending || proposal) return

    const message = input.trim()
    if (!message) {
      setError('Type what you want to change.')
      return
    }

    setIsSending(true)
    setError('')
    setNotice('')

    try {
      const result = await modifyTrip(trip.trip_id, message, trip)
      const diff = diffTrips(trip, result.trip)
      const reply =
        result.reply || (diff.hasChanges ? 'Here is a proposed change.' : 'No changes were needed.')

      setMessages((current) => [
        ...current,
        { role: 'user', text: message },
        { role: 'assistant', text: reply },
      ])
      setInput('')
      if (diff.hasChanges) setProposal({ trip: result.trip, diff })
    } catch (caught) {
      setError(caught.message)
    } finally {
      setIsSending(false)
    }
  }

  function handleApply() {
    onApply(proposal.trip)
    setProposal(null)
    setNotice('Plan updated. The itinerary and budget above now show the change.')
  }

  function handleDiscard() {
    setProposal(null)
    setNotice('Kept your current plan.')
  }

  return (
    <section aria-labelledby="assistant-heading" className="max-w-xl">
      <h2 id="assistant-heading" className="text-xl font-semibold">
        Change this plan
      </h2>
      <p className="mt-2 text-sm text-muted">
        Ask for a change in your own words. The assistant suggests a new plan, and nothing changes
        until you choose Apply.
      </p>
      {trip.is_mock && (
        <p className="mt-2 text-sm text-muted">
          Sample mode: replies are made up for testing and are not from a real AI.
        </p>
      )}

      {messages.length > 0 && (
        <div role="log" aria-live="polite" className="mt-4 space-y-3">
          {messages.map((message, index) => (
            <p key={index} className={message.role === 'user' ? 'text-ink' : 'text-muted'}>
              <span className="font-medium text-ink">
                {message.role === 'user' ? 'You: ' : 'Assistant: '}
              </span>
              {message.text}
            </p>
          ))}
        </div>
      )}

      {proposal && (
        <>
          <ChangeList diff={proposal.diff} currency={trip.currency} />
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleApply}
              className="rounded bg-brand px-5 py-3 font-medium text-white hover:bg-brand-dark"
            >
              Apply changes
            </button>
            <button
              type="button"
              onClick={handleDiscard}
              className="rounded border border-line bg-white px-5 py-3 font-medium hover:border-ink"
            >
              Keep current plan
            </button>
          </div>
        </>
      )}

      {notice && (
        <p role="status" className="mt-3 text-sm font-medium text-brand">
          {notice}
        </p>
      )}

      <form onSubmit={handleSubmit} noValidate className="mt-4">
        <label htmlFor="chat-input" className="block font-medium">
          What would you like to change?
        </label>
        <textarea
          id="chat-input"
          rows={3}
          maxLength={MAX_LENGTH}
          value={input}
          disabled={isSending || Boolean(proposal)}
          onChange={(event) => {
            setInput(event.target.value)
            if (error) setError('')
          }}
          placeholder="For example, make this trip cheaper"
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? 'chat-error' : undefined}
          className="mt-2 w-full rounded border border-line bg-white px-3 py-2 text-ink placeholder:text-muted disabled:opacity-60"
        />
        {error && (
          <p id="chat-error" role="alert" className="mt-1 text-sm text-red-700">
            {error}
          </p>
        )}
        {proposal && (
          <p className="mt-1 text-sm text-muted">
            Apply or keep the current plan before asking for another change.
          </p>
        )}
        <button
          type="submit"
          disabled={isSending || Boolean(proposal)}
          className="mt-3 rounded bg-brand px-5 py-3 font-medium text-white hover:bg-brand-dark disabled:opacity-60"
        >
          {isSending ? 'Sending...' : 'Send'}
        </button>
      </form>
    </section>
  )
}