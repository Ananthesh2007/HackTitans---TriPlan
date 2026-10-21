import { useRef, useState } from 'react'

// Runs a search function and tracks its status: idle, loading, error, or done.
//
// The results of the last search are kept while a new one runs, so the page
// does not go blank when a filter changes and the search runs again.
export function useSearch(searchFn) {
  const [state, setState] = useState({ status: 'idle', data: null, message: '' })
  const lastParams = useRef(null)

  async function run(params) {
    lastParams.current = params
    setState((current) => ({ status: 'loading', data: current.data, message: '' }))
    try {
      const data = await searchFn(params)
      setState({ status: 'done', data, message: '' })
    } catch (error) {
      setState({ status: 'error', data: null, message: error.message })
    }
  }

  function retry() {
    if (lastParams.current) run(lastParams.current)
  }

  return [state, run, retry]
}
