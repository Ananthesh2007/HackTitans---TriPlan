import { CONCESSIONS } from '../utils/filters.js'

// A radio group for the concession categories.
//
// A traveller picks one category, because a ticket is booked for one
// concession. The "None" option is the default.
export default function ConcessionSelect({ value, onChange, name = 'concession' }) {
  const options = [{ value: '', label: 'None' }, ...CONCESSIONS]

  return (
    <fieldset>
      <legend className="font-medium">Concession (optional)</legend>
      <p className="mt-1 text-sm text-muted">
        Pick your category to see the fares and rates that offer that concession.
      </p>
      <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {options.map((option) => (
          <label
            key={option.value || 'none'}
            className="flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm"
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              className="size-4 accent-primary"
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
