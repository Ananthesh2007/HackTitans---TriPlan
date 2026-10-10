import { useState } from 'react'

const INTERESTS = [
  { value: 'nature', label: 'Nature' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'culture', label: 'Culture' },
  { value: 'history', label: 'History' },
  { value: 'beaches', label: 'Beaches' },
  { value: 'relaxation', label: 'Relaxation' },
  { value: 'shopping', label: 'Shopping' },
]

const DIETS = [
  { value: 'none', label: 'No preference' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'non-vegetarian', label: 'Non-vegetarian' },
]

// Order used to find the first invalid field and move focus to it.
const FIELD_ORDER = ['destination', 'travelDate', 'days', 'people', 'budget']

const INITIAL_VALUES = {
  origin: '',
  destination: '',
  travelDate: '',
  days: '3',
  people: '1',
  budget: '',
  interests: [],
  diet: 'none',
}

// Today's date as YYYY-MM-DD in the user's own time zone.
function todayString() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now - offset).toISOString().slice(0, 10)
}

function validate(values) {
  const errors = {}

  if (values.destination.trim().length < 2) {
    errors.destination = 'Enter the place you want to visit.'
  }

  if (!values.travelDate) {
    errors.travelDate = 'Choose your travel date.'
  } else if (values.travelDate < todayString()) {
    errors.travelDate = 'Choose today or a later date.'
  }

  const days = Number(values.days)
  if (!Number.isInteger(days) || days < 1 || days > 30) {
    errors.days = 'Enter a whole number of days from 1 to 30.'
  }

  const people = Number(values.people)
  if (!Number.isInteger(people) || people < 1 || people > 20) {
    errors.people = 'Enter a whole number of travellers from 1 to 20.'
  }

  const budget = Number(values.budget)
  if (!values.budget || !Number.isFinite(budget) || budget <= 0) {
    errors.budget = 'Enter a budget greater than 0.'
  }

  return errors
}

function Field({ id, label, error, children }) {
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

function inputClass(error) {
  const border = error ? 'border-red-700' : 'border-line'
  return `w-full rounded border ${border} bg-white px-3 py-2 text-ink placeholder:text-muted`
}

export default function TripForm({ onSubmit, isSubmitting = false }) {
  const [values, setValues] = useState(INITIAL_VALUES)
  const [errors, setErrors] = useState({})

  function handleChange(event) {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    if (errors[name]) {
      setErrors((current) => ({ ...current, [name]: undefined }))
    }
  }

  function toggleInterest(value) {
    setValues((current) => ({
      ...current,
      interests: current.interests.includes(value)
        ? current.interests.filter((item) => item !== value)
        : [...current.interests, value],
    }))
  }

  function fieldProps(name) {
    return {
      id: name,
      name,
      value: values[name],
      onChange: handleChange,
      'aria-invalid': errors[name] ? 'true' : 'false',
      'aria-describedby': errors[name] ? `${name}-error` : undefined,
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    const nextErrors = validate(values)
    setErrors(nextErrors)

    const firstInvalid = FIELD_ORDER.find((name) => nextErrors[name])
    if (firstInvalid) {
      document.getElementById(firstInvalid)?.focus()
      return
    }

    // Same field names as docs/api-contract.md
    const origin = values.origin.trim()
    onSubmit({
      ...(origin ? { origin } : {}),
      destination: values.destination.trim(),
      days: Number(values.days),
      budget: Number(values.budget),
      people: Number(values.people),
      travel_date: values.travelDate,
      interests: values.interests,
      diet: values.diet,
    })
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-6">
      <Field id="origin" label="Travelling from (optional)">
        <input
          type="text"
          placeholder="For example, Bengaluru"
          autoComplete="off"
          maxLength={80}
          className={inputClass(false)}
          {...fieldProps('origin')}
        />
      </Field>

      <Field id="destination" label="Destination" error={errors.destination}>
        <input
          type="text"
          placeholder="For example, Coorg"
          autoComplete="off"
          className={inputClass(errors.destination)}
          {...fieldProps('destination')}
        />
      </Field>

      <Field id="travelDate" label="Travel date" error={errors.travelDate}>
        <input
          type="date"
          min={todayString()}
          className={inputClass(errors.travelDate)}
          {...fieldProps('travelDate')}
        />
      </Field>

      <div className="grid gap-6 sm:grid-cols-2">
        <Field id="days" label="Number of days" error={errors.days}>
          <input
            type="number"
            min="1"
            max="30"
            inputMode="numeric"
            className={inputClass(errors.days)}
            {...fieldProps('days')}
          />
        </Field>

        <Field id="people" label="Number of travellers" error={errors.people}>
          <input
            type="number"
            min="1"
            max="20"
            inputMode="numeric"
            className={inputClass(errors.people)}
            {...fieldProps('people')}
          />
        </Field>
      </div>

      <Field id="budget" label="Total budget for the group (INR)" error={errors.budget}>
        <input
          type="number"
          min="1"
          inputMode="numeric"
          placeholder="For example, 15000"
          className={inputClass(errors.budget)}
          {...fieldProps('budget')}
        />
      </Field>

      <fieldset>
        <legend className="font-medium">Interests (optional)</legend>
        <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {INTERESTS.map(({ value, label }) => (
            <label key={value} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.interests.includes(value)}
                onChange={() => toggleInterest(value)}
                className="size-4 accent-brand"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <Field id="diet" label="Food preference">
        <select className={inputClass(false)} {...fieldProps('diet')}>
          {DIETS.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </Field>

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded bg-brand px-5 py-3 font-medium text-white hover:bg-brand-dark disabled:opacity-60"
      >
        {isSubmitting ? 'Generating itinerary...' : 'Generate itinerary'}
      </button>
    </form>
  )
}