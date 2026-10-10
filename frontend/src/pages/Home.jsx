import { Link } from 'react-router-dom'

const steps = [
  'Enter your destination, dates, number of travellers, budget, and interests.',
  'Review the day-by-day plan and its estimated costs. Ask the chat assistant to change anything.',
  'Search flights and hotels, then book on the airline or hotel website.',
]

export default function Home() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-16">
      <h1 className="max-w-2xl text-4xl font-semibold leading-tight">
        Day-by-day trip plans with an estimated budget
      </h1>
      <p className="mt-4 max-w-xl text-lg text-muted">
        Tell TriPlan where you are going and what you can spend. It builds an itinerary you can
        change by chatting, and sends you to airline and hotel websites to book.
      </p>
      <Link
        to="/plan"
        className="mt-8 inline-block rounded bg-brand px-5 py-3 font-medium text-white hover:bg-brand-dark"
      >
        Plan a trip
      </Link>

      <h2 className="mt-16 text-2xl font-semibold">How it works</h2>
      <ol className="mt-4 max-w-xl list-decimal space-y-3 pl-6 marker:text-muted">
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
    </section>
  )
}