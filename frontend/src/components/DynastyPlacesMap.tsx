'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { DynastyPlace } from '@/types'

interface DynastyPlacesMapProps {
  places: DynastyPlace[]
  selectedPlaceId?: string | null
  onSelectPlace?: (place: DynastyPlace) => void
}

// Fix Leaflet default icon URLs in Next.js runtime.
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const SELECTED_ICON = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  iconRetinaUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const TILE_PROVIDERS = [
  {
    name: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  {
    name: 'Carto Light',
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO',
  },
  {
    name: 'OpenTopoMap',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap',
  },
]

export default function DynastyPlacesMap({ places, selectedPlaceId, onSelectPlace }: DynastyPlacesMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const tileErrorCountRef = useRef(0)
  const [providerIndex, setProviderIndex] = useState(0)
  const [allProvidersFailed, setAllProvidersFailed] = useState(false)

  const mappable = useMemo(
    () => places.filter((place) => place.coordinates && Number.isFinite(place.coordinates.lat) && Number.isFinite(place.coordinates.lon)),
    [places]
  )

  const center: [number, number] =
    mappable.length > 0
      ? [mappable[0].coordinates!.lat, mappable[0].coordinates!.lon]
      : [35.86, 104.19]

  useEffect(() => {
    if (!selectedPlaceId || !mapRef.current) return
    const selected = mappable.find((place) => place.id === selectedPlaceId)
    if (!selected?.coordinates) return
    mapRef.current.flyTo([selected.coordinates.lat, selected.coordinates.lon], 10, { duration: 1.0 })
  }, [selectedPlaceId, mappable])

  const provider = TILE_PROVIDERS[providerIndex]

  const handleTileError = () => {
    if (allProvidersFailed) return
    tileErrorCountRef.current += 1

    // Avoid switching provider on a single transient tile miss.
    if (tileErrorCountRef.current < 4) return

    tileErrorCountRef.current = 0
    setProviderIndex((prev) => {
      if (prev < TILE_PROVIDERS.length - 1) {
        return prev + 1
      }
      setAllProvidersFailed(true)
      return prev
    })
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer center={center} zoom={5} style={{ width: '100%', height: '100%' }} ref={mapRef as any}>
        <TileLayer attribution={provider.attribution} url={provider.url} eventHandlers={{ tileerror: handleTileError }} />

        {mappable.map((place) => (
          <Marker
            key={place.id}
            position={[place.coordinates!.lat, place.coordinates!.lon]}
            icon={place.id === selectedPlaceId ? SELECTED_ICON : new L.Icon.Default()}
            eventHandlers={{ click: () => onSelectPlace?.(place) }}
          >
            <Popup className="wl-map-popup">
              <strong style={{ color: '#F7FAFF', fontWeight: 700 }}>{place.name}</strong>
              <br />
              <span style={{ color: 'rgba(226,234,248,0.9)', fontSize: 13 }}>{place.location}</span>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {allProvidersFailed && (
        <div
          style={{
            position: 'absolute',
            left: 12,
            right: 12,
            bottom: 12,
            padding: '8px 10px',
            borderRadius: 8,
            background: 'rgba(11, 15, 26, 0.86)',
            border: '1px solid rgba(255,255,255,0.18)',
            color: 'rgba(255,255,255,0.84)',
            fontSize: 12,
            zIndex: 500,
          }}
        >
          Basemap tiles are blocked by network. Place pins still work and can be selected.
        </div>
      )}
    </div>
  )
}
