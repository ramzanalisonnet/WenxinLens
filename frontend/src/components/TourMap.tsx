'use client'

import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { SiteInfo } from '@/types'

// Fix Leaflet's broken default icon path in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const SELECTED_ICON = new L.Icon({
  iconUrl:       'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  iconRetinaUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize:  [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

interface TourMapProps {
  sites:         SiteInfo[]
  selectedSite?: SiteInfo | null
  onSelectSite?: (site: SiteInfo) => void
}

export default function TourMap({ sites, selectedSite, onSelectSite }: TourMapProps) {
  const mapRef = useRef<L.Map | null>(null)

  // Fly to selected site when it changes
  useEffect(() => {
    if (selectedSite?.coordinates && mapRef.current) {
      mapRef.current.flyTo([selectedSite.coordinates.lat, selectedSite.coordinates.lon], 14, { duration: 1.2 })
    }
  }, [selectedSite])

  const center: [number, number] =
    sites.length > 0 && sites[0].coordinates
      ? [sites[0].coordinates.lat, sites[0].coordinates.lon]
      : [35.86, 104.19]

  return (
    <MapContainer
      center={center}
      zoom={5}
      style={{ width: '100%', height: '100%' }}
      ref={mapRef as any}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {sites.filter((site) => site.coordinates).map((site) => (
        <Marker
          key={site.site_id}
          position={[site.coordinates!.lat, site.coordinates!.lon]}
          icon={selectedSite?.site_id === site.site_id ? SELECTED_ICON : new L.Icon.Default()}
          eventHandlers={{ click: () => onSelectSite?.(site) }}
        >
          <Popup>
            <strong>{site.name}</strong>
            <br />
            <span style={{ color: '#888', fontSize: 12 }}>{site.name_zh}</span>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
