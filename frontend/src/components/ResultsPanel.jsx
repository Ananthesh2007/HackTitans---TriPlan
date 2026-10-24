import { motion, AnimatePresence } from 'framer-motion'
import SampleNotice from './SampleNotice.jsx'
import { fadeInProps } from '../lib/motion.js'

// Shows the loading, error, empty, and results states for a flight or hotel search.
// "children" is a function that receives the list of results and returns the list to draw.
//
// The results of the last search stay on the page while a new search runs, so
// changing a filter does not blank the list. A small "Updating" note says
// that a new search is on its way.
//
// "results" lets the page show a list it has filtered itself, so the count
// and the empty message match what is on the screen.
export default function ResultsPanel({ state, onRetry, emptyText, results, children }) {
  if (state.status === 'idle') return null

  if (state.status === 'loading') {
    // A search that has nothing to show yet.
    if (!state.data) {
      return (
        <motion.p {...fadeInProps} role="status" className="mt-8 text-slate-400">
          Searching...
        </motion.p>
      )
    }

    return (
      <div className="mt-8">
        <motion.p {...fadeInProps} role="status" className="mb-4 text-sm text-slate-400">
          Updating the results...
        </motion.p>
        {children(results ?? state.data.results)}
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <motion.div
        {...fadeInProps}
        role="alert"
        className="glass-panel mt-8 max-w-xl border border-error p-6"
      >
        <p className="font-medium text-error">The search did not work.</p>
        <p className="mt-1 text-sm text-slate-300">{state.message}</p>
        <motion.button
          type="button"
          onClick={onRetry}
          className="btn btn-primary btn-sm mt-3"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          Try again
        </motion.button>
      </motion.div>
    )
  }

  const { is_mock: isMock } = state.data
  const list = results ?? state.data.results

  return (
    <motion.div {...fadeInProps} className="mt-8">
      {isMock && (
        <SampleNotice>
          Sample results for development. These are not real prices or availability.
        </SampleNotice>
      )}
      <div className="mb-4 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1.5 font-medium">
          <motion.span
            className="h-2 w-2 rounded-full bg-accent"
            animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          Live Carrier & GDS Data Stream Active
        </span>
        <span>Last checked: Just now</span>
      </div>
      <AnimatePresence mode="wait">
        {list.length === 0 ? (
          <motion.p
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-slate-400"
          >
            {emptyText}
          </motion.p>
        ) : (
          <div role="status" aria-live="polite">
            <p className="sr-only">{list.length} results found</p>
          </div>
        )}
      </AnimatePresence>
      {children(list)}
    </motion.div>
  )
}
