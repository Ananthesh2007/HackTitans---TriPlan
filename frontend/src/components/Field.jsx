// A labelled form field with an error message underneath.
export default function Field({ id, label, error, children }) {
  return (
    <div>
      <label htmlFor={id} className="block font-medium">
        {label}
      </label>
      <div className="mt-2">{children}</div>
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  )
}

export function inputClass(error) {
  const border = error ? 'border-red-700' : 'border-line'
  return `w-full rounded border ${border} bg-white px-3 py-2 text-ink placeholder:text-muted`
}