import { useEffect, useRef } from 'react'

// Runs the search again when the filters change.
//
// The filters are applied twice on purpose: the backend applies them to the
// results it sends, and the page applies them again so the list updates
// straight away. Because of that, a filter that widens the search (for
// example turning "AC" into "Non-AC") needs fresh results from the server,
// so the search runs again when a filter changes.
//
// The run is delayed a little, so typing in the price boxes does not send
// a request for every keystroke.
export function useFilterRefresh(filters, concession, hasSearched, runSearch, buildParams) {
  // The latest functions, so a new function identity does not start the
  // search again. This is set before the effect below runs, because the
  // effects run in the order they are declared.
  const latest = useRef({ runSearch, buildParams })
  useEffect(() => {
    latest.current = { runSearch, buildParams }
  })

  // The filters that the last search was made with.
  const applied = useRef(null)

  useEffect(() => {
    if (!hasSearched) return undefined

    if (applied.current === null) {
      // The first search. Its filters are the ones it was made with.
      applied.current = { filters, concession }
      return undefined
    }

    if (applied.current.filters === filters && applied.current.concession === concession) {
      return undefined
    }

    applied.current = { filters, concession }

    const timer = setTimeout(() => {
      latest.current.runSearch(latest.current.buildParams())
    }, 400)

    return () => clearTimeout(timer)
  }, [filters, concession, hasSearched])
}
