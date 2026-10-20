import SampleNotice from './SampleNotice.jsx'

// Shows the loading, error, empty, and results states for a flight or hotel search.
// "children" is a function that receives the list of results and returns the list to draw.
export default function ResultsPanel({ state, onRetry, emptyText, children }) {
  if (state.status === 'idle') return null

  if (state.status === 'loading') {
    return (
      <p role="status" className="mt-8 text-muted">
        Searching...
      </p>
    )
  }

  if (state.status === 'error') {
    return (
      <div role="alert" className="panel mt-8 max-w-xl border border-error">
        <p className="font-medium text-error">The search did not work.</p>
        <p className="mt-1 text-sm">{state.message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="btn btn-primary btn-sm mt-3"
        >
          Try again
        </button>
      </div>
    )
  }

  const { results, is_mock: isMock } = state.data

  return (
    <div className="mt-8">
      {isMock && (
        <SampleNotice>
          Sample results for development. These are not real prices or availability.
        </SampleNotice>
      )}
      {results.length === 0 ? (
        <p className="text-muted">{emptyText}</p>
      ) : (
        <div role="status" aria-live="polite">
          <p className="sr-only">{results.length} results found</p>
        </div>
      )}
      {results.length > 0 && children(results)}
    </div>
  )
}