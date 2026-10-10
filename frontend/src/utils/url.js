// Only allow https links, so a bad value such as "javascript:..." can never become a link.
export function isSafeBookingUrl(value) {
  if (typeof value !== 'string') return false
  try {
    return new URL(value).protocol === 'https:'
  } catch {
    return false
  }
}