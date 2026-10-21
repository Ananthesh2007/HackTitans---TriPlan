import { useEffect, useMemo, useState } from 'react'
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// The tiles are dark, to match the rest of the interface. Set VITE_MAP_TILE_URL
// to use a different tile server.
const TILE_URL =
  import.meta.env.VITE_MAP_TILE_URL ||
  'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
const TILE_ATTRIBUTION =
  import.meta.env.VITE_MAP_TILE_ATTRIBUTION ||
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'

// A marker drawn as a numbered dot, so it matches the design system and
// needs no image files.
function stopIcon(order, active) {
  return L.divIcon({
    className: 'triplan-marker',
    html: `<span class="triplan-marker__dot${active ? ' triplan-marker__dot--active' : ''}">${order}</span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  })
}

// Fits the map to the stops. Leaflet only reads the bounds when the map is
// created, so this runs again whenever the stops change.
function FitToStops({ positions }) {
  const map = useMap()

  useEffect(() => {
    if (positions.length === 0) return
    if (positions.length === 1) {
      map.setView(positions[0], 13)
      return
    }
    map.fitBounds(positions, { padding: [48, 48], maxZoom: 14 })
  }, [map, positions])

  return null
}

function formatDistance(km) {
  if (typeof km !== 'number' || !Number.isFinite(km)) return ''
  if (km < 1) return `${Math.round(km * 1000)} m`
  return `${km.toFixed(1)} km`
}

function formatDuration(minutes) {
  if (typeof minutes !== 'number' || !Number.isFinite(minutes)) return ''
  if (minutes < 60) return `${Math.round(minutes)} min`
  const hours = Math.floor(minutes / 60)
  const rest = Math.round(minutes % 60)
  return rest ? `${hours} h ${rest} min` : `${hours} h`
}

// One day's map: the stops on the map, and the same stops listed below.
function DayMap({ day }) {
  const stops = Array.isArray(day.stops) ? day.stops : []
  const located = stops.filter((stop) => stop.coordinates)

  const positions = useMemo(
    () => located.map((stop) => [stop.coordinates.lat, stop.coordinates.lng]),
    [located],
  )

  const routePoints = useMemo(() => {
    const points = Array.isArray(day.route?.points) ? day.route.points : []
    if (points.length < 2) return positions
    return points.map((point) => [point.lat, point.lng])
  }, [day.route, positions])

  const route = day.route
  const distance = formatDistance(route?.distance_km)
  const duration = formatDuration(route?.duration_minutes)

  if (located.length === 0) {
    return (
      <div className="panel">
        <p className="text-muted">
          None of the places in this day could be found on the map.
        </p>
        {day.warning && <p className="mt-2 text-sm text-muted">{day.warning}</p>}
      </div>
    )
  }

  return (
    <div>
      <div className="overflow-hidden rounded-lg border border-line">
        <MapContainer
          center={positions[0]}
          zoom={13}
          scrollWheelZoom={false}
          className="h-88 w-full"
        >
          <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
          <FitToStops positions={positions} />

          {routePoints.length > 1 && (
            <Polyline
              positions={routePoints}
              pathOptions={{ color: '#e05a62', weight: 3, opacity: 0.9 }}
            />
          )}

          {located.map((stop) => (
            <Marker
              key={`${stop.order}-${stop.name}`}
              position={[stop.coordinates.lat, stop.coordinates.lng]}
              icon={stopIcon(stop.order, false)}
            >
              <Popup>
                <span className="font-semibold">{stop.name}</span>
                <br />
                {stop.location}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {(distance || duration) && (
        <p className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {distance && (
            <span className="text-ink">
              <span className="text-muted">Total distance:</span> {distance}
            </span>
          )}
          {duration && (
            <span className="text-ink">
              <span className="text-muted">Travel time:</span> {duration}
            </span>
          )}
          {route?.is_estimate && (
            <span className="chip">Estimate</span>
          )}
        </p>
      )}

      {route?.warning && <p className="mt-1 text-sm text-muted">{route.warning}</p>}

      <ol className="mt-4 divide-y divide-line border-y border-line">
        {stops.map((stop) => (
          <li
            key={`${stop.order}-${stop.name}`}
            className="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <div className="flex items-start gap-3">
              <span
                aria-hidden="true"
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-on-primary"
              >
                {stop.order}
              </span>
              <div>
                <p className="font-medium">{stop.name}</p>
                <p className="text-sm text-muted">{stop.location}</p>
              </div>
            </div>
            {stop.map_url ? (
              <a
                href={stop.map_url}
                target="_blank"
                rel="noreferrer noopener"
                className="btn btn-secondary btn-sm"
              >
                Open in map
                <span className="sr-only"> for {stop.name}</span>
              </a>
            ) : (
              <span className="text-sm text-muted">Not on the map</span>
            )}
          </li>
        ))}
      </ol>

      {day.warning && <p className="mt-3 text-sm text-muted">{day.warning}</p>}
    </div>
  )
}

// Shows the map of every day of a trip. The days are shown one at a time,
// so the map stays readable on a phone.
export default function MapView({ map, isLoading, error }) {
  // null means "the first day". A specific number means the user picked one.
  const [pickedDay, setPickedDay] = useState(null)

  const days = useMemo(() => (Array.isArray(map?.days) ? map.days : []), [map])

  // The picked day falls back to the first one when the plan changes and
  // the picked day is no longer there.
  const current =
    days.find((day) => day.day === pickedDay) || days[0] || null

  if (isLoading) {
    return (
      <section aria-labelledby="map-heading" className="max-w-3xl">
        <h2 id="map-heading" className="text-xl font-black">
          Map
        </h2>
        <p role="status" className="mt-2 text-muted">
          Looking up the places in your plan...
        </p>
      </section>
    )
  }

  if (error) {
    return (
      <section aria-labelledby="map-heading" className="max-w-3xl">
        <h2 id="map-heading" className="text-xl font-black">
          Map
        </h2>
        <p role="alert" className="mt-2 text-muted">
          {error}
        </p>
      </section>
    )
  }

  const hasStops = days.some((day) => (day.stops || []).some((stop) => stop.coordinates))

  return (
    <section aria-labelledby="map-heading" className="max-w-3xl">
      <h2 id="map-heading" className="text-xl font-black">
        Map
      </h2>
      <p className="mt-2 text-sm text-muted">
        Where your plan takes you, and how far apart the places are.
      </p>

      {map?.is_mock && map?.warning && (
        <p className="mt-3 rounded-lg bg-card px-4 py-3 text-sm text-muted">{map.warning}</p>
      )}

      {!hasStops ? (
        <p className="mt-4 text-muted">
          None of the places in this plan could be found on the map.
        </p>
      ) : (
        <>
          {days.length > 1 && (
            <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Days">
              {days.map((day) => (
                <button
                  key={day.day}
                  type="button"
                  role="tab"
                  aria-selected={current?.day === day.day}
                  onClick={() => setPickedDay(day.day)}
                  className={`chip ${
                    current?.day === day.day
                      ? 'bg-ink text-primary'
                      : 'bg-primary text-on-primary'
                  }`}
                >
                  Day {day.day}
                </button>
              ))}
            </div>
          )}

          <div className="mt-4">
            {current && <DayMap key={current.day} day={current} />}
          </div>
        </>
      )}
    </section>
  )
}
