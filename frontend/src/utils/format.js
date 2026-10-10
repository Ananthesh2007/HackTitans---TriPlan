// Formats a number as money, for example 13600 becomes ₹13,600 for INR.
export function formatMoney(amount, currency = 'INR') {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}