// Banner shown whenever the data on screen is sample data and not real.
export default function SampleNotice({ children }) {
  return (
    <p className="mb-6 max-w-xl border border-line bg-white px-4 py-3 text-sm">{children}</p>
  )
}