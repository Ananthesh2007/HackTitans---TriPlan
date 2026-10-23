import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { geocodePlace } from '../services/api.js'
import { searchPlaces, searchPopular } from '../utils/places.js'
import { inputClass } from './Field.jsx'

// A text box that suggests places as the user types.
//
// The suggestions come from two places:
// - a small bundled list of cities and airports, so the box is useful
//   straight away and does not need the network;
// - the backend's geocoding endpoint, so a place that is not in the list
//   can still be found.
//
// The list is a list of combobox options, so it follows the ARIA pattern
// for a combobox: the text box keeps its own value, and the options are
// picked with the arrow keys, Enter, or a click.

const LOOKUP_DELAY_MS = 350

function LocationIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      className="mt-0.5 size-5 shrink-0 text-accent"
    >
      <path
        d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  )
}

export default function PlaceInput({
  id,
  value,
  onChange,
  onBlur,
  error,
  placeholder = 'City or town',
  label,
  describedBy,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [options, setOptions] = useState([])
  const [activeIndex, setActiveIndex] = useState(-1)
  const [isLoading, setIsLoading] = useState(false)

  const listId = useId()
  const rootRef = useRef(null)
  const inputRef = useRef(null)
  const skipLookup = useRef(false)
  // The text the last lookup was made for, so a stale answer is not shown
  // next to the new suggestions.
  const lookedUp = useRef('')

  // The bundled suggestions for what has been typed, plus the popular
  // cities that appear before anything is typed.
  const localOptions = useMemo(() => (value.trim() ? searchPlaces(value) : searchPopular()), [value])

  // Ask the backend about the place once the typing has settled. A place
  // that is already in the bundled list does not need the lookup.
  useEffect(() => {
    const text = value.trim()

    if (text.length < 3 || skipLookup.current) {
      setOptions([])
      lookedUp.current = ''
      return undefined
    }

    // The answer for the old text is no longer wanted.
    setOptions([])

    const timer = setTimeout(() => {
      setIsLoading(true)
      geocodePlace(text)
        .then((data) => {
          // The user may have typed on while the answer was on its way.
          if (lookedUp.current !== text) return
          const name = data?.name || data?.display_name
          if (!name || data?.error) return
          setOptions([
            {
              value: name,
              label: name,
              secondary:
                data?.display_name && data.display_name !== name
                  ? data.display_name
                  : 'From the map',
            },
          ])
        })
        .catch(() => {
          // A place that cannot be looked up is not an error the user can
          // do anything about, so the list simply stays as it is.
        })
        .finally(() => {
          if (lookedUp.current === text) setIsLoading(false)
        })
    }, LOOKUP_DELAY_MS)

    lookedUp.current = text

    return () => clearTimeout(timer)
  }, [value])

  // Close the list when the user clicks somewhere else.
  useEffect(() => {
    function handlePointerDown(event) {
      if (!rootRef.current?.contains(event.target)) setIsOpen(false)
    }
    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [])

  // Keep the option the keyboard is on inside the scroll box.
  useEffect(() => {
    if (activeIndex < 0) return
    document.getElementById(`${listId}-option-${activeIndex}`)?.scrollIntoView({
      block: 'nearest',
    })
  }, [activeIndex, listId])

  const visibleOptions = isOpen ? [...localOptions, ...options] : []

  function openList() {
    setIsOpen(true)
    setActiveIndex(-1)
  }

  function choose(option) {
    skipLookup.current = true
    setOptions([])
    setIsOpen(false)
    setActiveIndex(-1)
    onChange(option.value)
  }

  function handleChange(event) {
    skipLookup.current = false
    setOptions([])
    onChange(event.target.value)
    setIsOpen(true)
    setActiveIndex(-1)
  }

  function handleKeyDown(event) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (!isOpen) {
        openList()
        return
      }
      setActiveIndex((current) => {
        if (visibleOptions.length === 0) return -1
        return (current + 1) % visibleOptions.length
      })
      return
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((current) => {
        if (visibleOptions.length === 0) return -1
        return current <= 0 ? visibleOptions.length - 1 : current - 1
      })
      return
    }

    if (event.key === 'Enter') {
      if (isOpen && activeIndex >= 0 && visibleOptions[activeIndex]) {
        event.preventDefault()
        choose(visibleOptions[activeIndex])
      }
      return
    }

    if (event.key === 'Escape') {
      setIsOpen(false)
      setActiveIndex(-1)
    }
  }

  function handleBlur() {
    setIsOpen(false)
    setActiveIndex(-1)
    onBlur?.()
  }

  // The hint under the box. It only appears once the typing has settled,
  // so it does not flash while the user is still typing.
  const hasTyped = value.trim().length >= 3
  const showStatus =
    isLoading || (hasTyped && !isOpen && visibleOptions.length === 0 && !isLoading)

  return (
    <div ref={rootRef} className="relative">
      <input
        ref={inputRef}
        type="text"
        id={id}
        name={id}
        value={value}
        onChange={handleChange}
        onFocus={openList}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoComplete="off"
        role="combobox"
        aria-expanded={isOpen && visibleOptions.length > 0}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          activeIndex >= 0 ? `${listId}-option-${activeIndex}` : undefined
        }
        aria-label={label}
        aria-describedby={describedBy}
        aria-invalid={error ? 'true' : 'false'}
        className={inputClass(error)}
      />

      {isOpen && visibleOptions.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          aria-label={label ? `${label} suggestions` : 'Suggestions'}
          className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-line bg-card py-1 shadow-lg"
        >
          {visibleOptions.map((option, index) => (
            <li
              key={`${option.value}-${index}`}
              id={`${listId}-option-${index}`}
              role="option"
              aria-selected={index === activeIndex}
            >
              <button
                type="button"
                // The mouse down runs before the blur, so the click is not
                // lost when the list closes.
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(option)}
                className={`flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-surface ${
                  index === activeIndex ? 'bg-surface' : ''
                }`}
              >
                <LocationIcon />
                <span className="flex min-w-0 flex-col gap-0.5">
                  <span className="truncate font-medium text-ink">{option.label}</span>
                  {option.secondary && (
                    <span className="truncate text-xs text-muted">{option.secondary}</span>
                  )}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {showStatus && (
        <p className="mt-1 text-xs text-muted" role="status">
          {isLoading ? 'Looking up places...' : 'No matching place. You can still type it in.'}
        </p>
      )}
    </div>
  )
}
