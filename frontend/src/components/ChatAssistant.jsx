import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { modifyTripStream } from '../services/api.js'
import { diffTrips } from '../utils/diffTrips.js'
import { formatMoney } from '../utils/format.js'
import { fadeInProps, staggerContainer, staggerItem } from '../lib/motion.js'

const MAX_LENGTH = 500

const SUGGESTIONS = [
  '✨ Make it cheaper',
  '🌿 Add relaxing nature spots',
  '🍲 Recommend local food spots',
  '🧳 What should I pack for this trip?',
]

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

// Conversational AI co-pilot that helps users plan, adjust, and explore their trip.
export default function ChatAssistant({ trip, onApply }) {
  const [messages, setMessages] = useState([])
  const [streamingText, setStreamingText] = useState('')
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [proposal, setProposal] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText, isSending])

  async function handleSubmit(event) {
    if (event) event.preventDefault()
    if (isSending || proposal) return

    const message = input.trim()
    if (!message) {
      setError('Type what you want to change or ask.')
      return
    }

    setIsSending(true)
    setStreamingText('')
    setError('')
    setNotice('')

    const nextMessages = [...messages, { role: 'user', text: message }]
    setMessages(nextMessages)
    setInput('')

    const history = messages.map((m) => ({
      role: m.role,
      content: m.text,
    }))

    try {
      let accumulatedReply = ''
      await modifyTripStream(
        trip.trip_id,
        message,
        trip,
        history,
        (token) => {
          accumulatedReply += token
          setStreamingText(accumulatedReply)
        },
        (doneResult) => {
          const diff = diffTrips(trip, doneResult.trip)
          const finalReply =
            doneResult.reply ||
            accumulatedReply ||
            (diff.hasChanges ? 'Here is a proposed change.' : 'No changes were needed.')

          setMessages([...nextMessages, { role: 'assistant', text: finalReply }])
          setStreamingText('')
          if (diff.hasChanges) setProposal({ trip: doneResult.trip, diff })
        },
        (err) => {
          setError(err.message || 'Something went wrong. Please try again.')
          setStreamingText('')
        },
      )
    } catch (caught) {
      setError(caught.message || 'Could not connect to the assistant.')
      setStreamingText('')
    } finally {
      setIsSending(false)
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSubmit(event)
    }
  }

  function handleClearChat() {
    setMessages([])
    setStreamingText('')
    setError('')
    setProposal(null)
    setNotice('Conversation cleared.')
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
      <div className="flex items-center justify-between">
        <h2 id="assistant-heading" className="text-xl font-black text-slate-100">
          Trip Co-Pilot
        </h2>
        {messages.length > 0 && !isSending && !proposal && (
          <button
            type="button"
            onClick={handleClearChat}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            Clear conversation
          </button>
        )}
      </div>

      <p className="mt-2 text-sm text-slate-400">
        Chat naturally with your AI travel co-pilot to tweak activities, reduce costs, or explore recommendations.
      </p>
      {trip.is_mock && (
        <p className="mt-1 text-xs text-slate-500">
          Sample mode: simulated co-pilot responses for testing.
        </p>
      )}

      <AnimatePresence mode="popLayout">
        {(messages.length > 0 || isSending) && (
          <motion.div
            role="log"
            aria-live="polite"
            className="mt-4 space-y-3 glass-panel p-4 scrollbar-custom max-h-96 overflow-y-auto"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <span className="text-xs font-semibold mb-1 text-slate-400">
                  {message.role === 'user' ? 'You' : 'TriPlan Co-Pilot'}
                </span>
                <div
                  className={`rounded-2xl p-3.5 text-sm leading-relaxed whitespace-pre-wrap max-w-[90%] ${
                    message.role === 'user'
                      ? 'bg-accent/15 border border-accent/30 text-slate-100 rounded-tr-sm'
                      : 'bg-surface/90 border border-slate-700/60 text-slate-200 rounded-tl-sm'
                  }`}
                >
                  {message.text}
                </div>
              </motion.div>
            ))}

            {isSending && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-start"
              >
                <span className="text-xs font-semibold mb-1 text-accent flex items-center gap-1.5">
                  <span className="inline-block w-2 h-2 rounded-full bg-accent animate-ping" />
                  TriPlan Co-Pilot
                </span>
                <div className="bg-surface/90 border border-slate-700/60 text-slate-200 rounded-2xl rounded-tl-sm p-3.5 text-sm leading-relaxed whitespace-pre-wrap max-w-[90%]">
                  {streamingText ? (
                    <>
                      {streamingText}
                      <span className="inline-block w-1.5 h-4 ml-1 bg-accent animate-pulse align-middle" />
                    </>
                  ) : (
                    <span className="text-slate-400 italic">Thinking...</span>
                  )}
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
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

      {!isSending && !proposal && (
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                const text = suggestion.replace(/^[^\w]+/, '').trim()
                setInput(text)
              }}
              className="text-xs px-2.5 py-1 rounded-full bg-surface border border-slate-700/80 hover:border-accent/60 text-slate-300 hover:text-slate-100 transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="mt-3">
        <label htmlFor="chat-input" className="block font-medium text-sm text-slate-200">
          Message Co-Pilot
        </label>
        <textarea
          id="chat-input"
          rows={3}
          maxLength={MAX_LENGTH}
          value={input}
          disabled={isSending || Boolean(proposal)}
          onKeyDown={handleKeyDown}
          onChange={(event) => {
            setInput(event.target.value)
            if (error) setError('')
          }}
          placeholder="Ask a question or request a change (e.g. 'Can we visit local viewpoints on day 2?')"
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? 'chat-error' : undefined}
          className="input mt-1.5 disabled:opacity-60"
        />
        {error && (
          <p id="chat-error" role="alert" className="mt-1 text-sm text-error">
            {error}
          </p>
        )}
        {proposal && (
          <p className="mt-1 text-sm text-muted">
            Apply or keep the current plan before sending another message.
          </p>
        )}
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-slate-500">
            Press <kbd className="px-1.5 py-0.5 rounded bg-surface border border-slate-700 text-slate-300">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-surface border border-slate-700 text-slate-300">Shift + Enter</kbd> for new line
          </span>
          <motion.button
            type="submit"
            disabled={isSending || Boolean(proposal)}
            className="btn btn-primary"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isSending ? 'Sending...' : 'Send'}
          </motion.button>
        </div>
      </form>
    </motion.section>
  )
}