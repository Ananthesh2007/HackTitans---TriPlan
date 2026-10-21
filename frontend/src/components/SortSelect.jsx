// The "Sort by" control that sits above the results.
export default function SortSelect({ value, options, onChange, resultCount }) {
  return (
    <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-muted" role="status" aria-live="polite">
        {resultCount} {resultCount === 1 ? 'result' : 'results'}
      </p>
      <div className="flex items-center gap-2">
        <label htmlFor="sort-results" className="text-sm text-muted">
          Sort by
        </label>
        <select
          id="sort-results"
          name="sort-results"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="input w-auto"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
