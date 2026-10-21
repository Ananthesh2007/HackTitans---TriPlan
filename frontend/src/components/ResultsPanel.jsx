import SampleNotice from './SampleNotice.jsx'

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
        <p role="status" className="mt-8 text-muted">
          Searching...
        </p>
      )
    }

    return (
      <div className="mt-8">
        <p role="status" className="mb-4 text-sm text-muted">
          Updating the results...
        </p>
        {children(results ?? state.data.results)}
      </div>
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

  const { is_mock: isMock } = state.data
  const list = results ?? state.data.results

  return (
    <div className="mt-8">
      {isMock && (
        <SampleNotice>
          Sample results for development. These are not real prices or availability.
        </SampleNotice>
      )}
      {list.length === 0 ? (
        <p className="text-muted">{emptyText}</p>
      ) : (
        <div role="status" aria-live="polite">
          <p className="sr-only">{list.length} results found</p>
        </div>
      )}
      {children(list)}
    </div>
  )
}
