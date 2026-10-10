const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/

// Today's date as YYYY-MM-DD in the user's own time zone.
export function todayString() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now - offset).toISOString().slice(0, 10)
}

// True for a real calendar date written as YYYY-MM-DD.
export function isDateString(value) {
  if (typeof value !== 'string' || !DATE_PATTERN.test(value)) return false
  const date = new Date(`${value}T00:00:00Z`)
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value
}

// Adds a number of days to a YYYY-MM-DD date and returns a YYYY-MM-DD date.
export function addDays(dateString, days) {
  const date = new Date(`${dateString}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

// Turns 2026-11-20 into "20 Nov 2026". Returns an empty string for anything else.
export function formatDate(dateString) {
  if (!isDateString(dateString)) return ''
  return new Date(`${dateString}T00:00:00Z`).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}