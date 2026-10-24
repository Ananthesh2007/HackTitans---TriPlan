import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { modifyTrip } from '../services/api.js'
import { diffTrips } from '../utils/diffTrips.js'
import { formatMoney } from '../utils/format.js'
import { fadeInProps, staggerContainer, staggerItem } from '../lib/motion.js'

const MAX_LENGTH = 500

function ChangeList({ diff, currency }) {
  const hasTotals = diff.totalBefore !== null && diff.totalAfter !== null

  return (
    <motion.div {...fadeInProps} className="glass-panel mt-3 p-4">
      <h3 className="text-lg font-black text-slate-100">Proposed changes</h3>
      <motion.ul
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="mt-3 space-y-2 text-sm scrollbar-custom max-h-60 overflow-y-auto"
      >
        {diff.removed.map((item) => (
          <motion.li
            key={`r-${item.day}-${item.name}`}
            variants={staggerItem}
            className="text-error flex items-start gap-2"
          >
            <span className="text-error">−</span>
            <span>Remove: {item.name} (day {item.day}, {formatMoney(item.cost, currency)})</span>
          </motion.li>
        ))}
        {diff.added.map((item) => (
          <motion.li
            key={`a-${item.day}-${item.name}`}
            variants={staggerItem}
            className="text-accent flex items-start gap-2"
          >
            <span className="text-accent">+</span>
            <span>Add: {item.name} (day {item.day}, {formatMoney(item.cost, currency)})</span>
          </motion.li>
        ))}
        {diff.changed.map((item) => (
          <motion.li
            key={`c-${item.day}-${item.name}`}
            variants={staggerItem}
            className="text-slate-300 flex items-start gap-2"
          >
            <span className="text-secondary">→</span>
            <span>Change: {item.name} (day {item.day}), cost {formatMoney(item.oldCost, currency)} to{' '}
            {formatMoney(item.cost, currency)}</span>
          </motion.li>
        ))}
      </motion.ul>
      {hasTotals && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-3 font-medium text-slate-100"
        >
          Estimated total: <span className="text-error">{formatMoney(diff.totalBefore, currency)}</span> → <span className="text-accent">{formatMoney(diff.totalAfter, currency)}</span>
        </motion.p>
      )}
    </motion.div>
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
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      aria-labelledby="assistant-heading"
      className="max-w-xl"
    >
      <h2 id="assistant-heading" className="text-xl font-black text-slate-100">
        Change this plan
      </h2>
      <p className="mt-2 text-sm text-slate-400">
        Ask for a change in your own words. The assistant suggests a new plan, and nothing changes
        until you choose Apply.
      </p>
      {trip.is_mock && (
        <p className="mt-2 text-sm text-slate-400">
          Sample mode: replies are made up for testing and are not from a real AI.
        </p>
      )}

      <AnimatePresence mode="wait">
        {messages.length > 0 && (
          <motion.div
            role="log"
            aria-live="polite"
            className="mt-4 space-y-3 glass-panel p-4 scrollbar-custom max-h-80 overflow-y-auto"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            {messages.map((message, index) => (
              <motion.p
                key={index}
                initial={{ opacity: 0, x: message.role === 'user' ? 20 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={message.role === 'user' ? 'text-slate-100' : 'text-slate-300'}
              >
                <span className="font-medium text-accent">
                  {message.role === 'user' ? 'You: ' : 'Assistant: '}
                </span>
                {message.text}
              </motion.p>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {proposal && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <ChangeList diff={proposal.diff} currency={trip.currency} />
            <div className="mt-3 flex flex-wrap gap-3">
              <motion.button
                type="button"
                onClick={handleApply}
                className="btn btn-primary"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Apply changes
              </motion.button>
              <motion.button
                type="button"
                onClick={handleDiscard}
                className="btn btn-secondary"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Keep current plan
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {notice && (
          <motion.p
            role="status"
            className="mt-3 text-sm font-medium text-accent"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {notice}
          </motion.p>
        )}
      </AnimatePresence>

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
          className="input mt-2 disabled:opacity-60"
        />
        {error && (
          <p id="chat-error" role="alert" className="mt-1 text-sm text-error">
            {error}
          </p>
        )}
        {proposal && (
          <p className="mt-1 text-sm text-muted">
            Apply or keep the current plan before asking for another change.
          </p>
        )}
        <motion.button
          type="submit"
          disabled={isSending || Boolean(proposal)}
          className="btn btn-primary mt-3"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {isSending ? 'Sending...' : 'Send'}
        </motion.button>
      </form>
    </motion.section>
  )
}