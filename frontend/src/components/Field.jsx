// A labelled form field with an error message underneath.
export default function Field({ id, label, error, children }) {
  return (
    <div>
      <label htmlFor={id} className="block font-medium">
        {label}
      </label>
      <div className="mt-2">{children}</div>
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1 text-sm text-error">
          {error}
        </p>
      )}
    </div>
  )
}

export function inputClass(error) {
  return error ? 'input border-error' : 'input'
}