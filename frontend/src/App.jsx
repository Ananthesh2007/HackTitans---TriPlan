import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import Home from './pages/Home.jsx'
import Plan from './pages/Plan.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Flights from './pages/Flights.jsx'
import Hotels from './pages/Hotels.jsx'

// Temporary page for routes that are built later in the schedule.
function UnderConstruction({ title }) {
  return (
    <section className="mx-auto max-w-5xl px-4 py-16">
      <h1 className="text-3xl font-semibold">{title}</h1>
      <p className="mt-3 text-muted">This page is not built yet.</p>
    </section>
  )
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/plan" element={<Plan />} />
          <Route path="/trips/:tripId" element={<Dashboard />} />
          <Route path="/flights" element={<Flights />} />
          <Route path="/hotels" element={<Hotels />} />
          <Route path="/privacy" element={<UnderConstruction title="Privacy Policy" />} />
          <Route path="/terms" element={<UnderConstruction title="Terms and Conditions" />} />
          <Route path="*" element={<UnderConstruction title="Page not found" />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}