// Formats a number as money, for example 13600 becomes ₹13,600 for INR.
// Returns an empty string for values that are not numbers.
export function formatMoney(amount, currency) {
  const value = Number(amount)
  if (amount === null || amount === undefined || !Number.isFinite(value)) return ''

  const code = currency || 'INR'
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: code,
      maximumFractionDigits: 0,
    }).format(value)
  } catch {
    // Unknown currency code: show the number with the code instead of crashing.
    return `${code} ${Math.round(value).toLocaleString('en-IN')}`
  }
}