import { isDateString, todayString } from './dates.js'

// Helpers that turn values from the page address into safe starting values for a form.

export function cleanText(value) {
  return typeof value === 'string' ? value.trim().slice(0, 80) : ''
}

// A valid date that is today or later, otherwise an empty string.
export function cleanDate(value) {
  return isDateString(value) && value >= todayString() ? value : ''
}

// A whole number between min and max, otherwise the fallback.
export function cleanCount(value, min, max, fallback) {
  const number = Number(value)
  return Number.isInteger(number) && number >= min && number <= max ? number : fallback
}

// A known concession category, otherwise an empty string.
export function cleanConcession(value) {
  const known = ['senior_citizen', 'army', 'student', 'doctor', 'nurse']
  return typeof value === 'string' && known.includes(value) ? value : ''
}