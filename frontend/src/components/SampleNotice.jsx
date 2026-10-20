// Banner shown whenever the data on screen is sample data and not real.
export default function SampleNotice({ children }) {
  return (
    <p className="mb-6 max-w-xl rounded-lg bg-card px-4 py-3 text-sm text-muted">{children}</p>
  )
}