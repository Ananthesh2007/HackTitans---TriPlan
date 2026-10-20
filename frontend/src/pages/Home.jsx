import { Link } from 'react-router-dom'

const steps = [
  'Enter your destination, dates, number of travellers, budget, and interests.',
  'Review the day-by-day plan and its estimated costs. Ask the chat assistant to change anything.',
  'Search flights and hotels, then book on the airline or hotel website.',
]

export default function Home() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-16">
      <h1 className="headline-display max-w-3xl">
        Day-by-day trip plans with an estimated budget
      </h1>
      <p className="body-lg mt-4 max-w-xl text-muted">
        Tell TriPlan where you are going and what you can spend. It builds an itinerary you can
        change by chatting, and sends you to airline and hotel websites to book.
      </p>
      <Link to="/plan" className="btn btn-primary mt-8">
        Plan a trip
      </Link>

      <h2 className="headline-md mt-16">How it works</h2>
      <ol className="mt-4 max-w-xl list-decimal space-y-3 pl-6 marker:text-muted">
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
    </section>
  )
}