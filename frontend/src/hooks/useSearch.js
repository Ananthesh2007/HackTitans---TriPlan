import { useRef, useState } from 'react'

// Runs a search function and tracks its status: idle, loading, error, or done.
export function useSearch(searchFn) {
  const [state, setState] = useState({ status: 'idle', data: null, message: '' })
  const lastParams = useRef(null)

  async function run(params) {
    lastParams.current = params
    setState({ status: 'loading', data: null, message: '' })
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