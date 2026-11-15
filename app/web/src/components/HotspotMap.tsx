import { useEffect, useRef, useState } from 'react'
import maplibregl, { type GeoJSONSource } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { HotspotCollection, HotspotFeature } from '../lib/types'
import { Crosshair, ZoomIn, ZoomOut } from 'lucide-react'

type MapProps = {
  detections: HotspotCollection | null
  onSelect: (record: HotspotFeature | null) => void
  onViewport: (bbox: string) => void
  focusedId: string | number | null
}

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

export default function HotspotMap({ detections, onSelect, onViewport, focusedId }: MapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const recordsRef = useRef<HotspotCollection | null>(null)
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const [ready, setReady] = useState(false)
  const onSelectRef = useRef(onSelect)
  const onViewportRef = useRef(onViewport)
  onSelectRef.current = onSelect
  onViewportRef.current = onViewport
  recordsRef.current = detections

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: containerRef.current, style: MAP_STYLE, center: [117.8, -2.5], zoom: 3.8,
      minZoom: 2.2, maxZoom: 14, maxBounds: [[90, -16], [145, 11]], attributionControl: false,
    })
    mapRef.current = map
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')
    const publishBounds = () => {
      const b = map.getBounds()
      onViewportRef.current([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map(x => x.toFixed(4)).join(','))
    }
    map.on('load', () => {
      map.addSource('hotspots', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, cluster: true, clusterMaxZoom: 8, clusterRadius: 42 })
      map.addLayer({ id: 'hotspot-halo', type: 'circle', source: 'hotspots', filter: ['has', 'point_count'],
        paint: { 'circle-color': '#ad392e', 'circle-opacity': 0.10, 'circle-radius': ['step', ['get', 'point_count'], 21, 12, 27, 40, 35] } })
      map.addLayer({ id: 'hotspot-clusters', type: 'circle', source: 'hotspots', filter: ['has', 'point_count'],
        paint: { 'circle-color': '#c94a3f', 'circle-opacity': .86, 'circle-stroke-color': '#f7a196', 'circle-stroke-width': .85,
          'circle-radius': ['step', ['get', 'point_count'], 10, 12, 14, 40, 19] } })
      map.addLayer({ id: 'hotspot-cluster-count', type: 'symbol', source: 'hotspots', filter: ['has', 'point_count'],
        layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-size': 10, 'text-font': ['Open Sans Regular'] },
        paint: { 'text-color': '#fff0e9' } })
      map.addLayer({ id: 'hotspot-points', type: 'circle', source: 'hotspots', filter: ['!', ['has', 'point_count']],
        paint: { 'circle-color': '#e34b3f', 'circle-opacity': .92,
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 3, 3.2, 8, 5.2, 12, 7],
          'circle-stroke-color': '#ffd0bc', 'circle-stroke-width': .75 } })
      map.on('click', 'hotspot-clusters', async (e) => {
        const first = map.queryRenderedFeatures(e.point, { layers: ['hotspot-clusters'] })[0]
        if (!first || !first.properties) return
        const id = Number(first.properties.cluster_id)
        try {
          const zoom = await (map.getSource('hotspots') as GeoJSONSource).getClusterExpansionZoom(id)
          map.easeTo({ center: (first.geometry as { coordinates: [number, number] }).coordinates, zoom: Math.min(zoom, 13), duration: 500 })
        } catch { /* map may be closing */ }
      })
      map.on('click', 'hotspot-points', (e) => {
        const f = e.features?.[0]
        const id = f?.properties?.id
        const record = recordsRef.current?.features.find(r => String(r.properties.id) === String(id))
        if (record) onSelectRef.current(record)
      })
      map.on('click', (e) => {
        const points = map.queryRenderedFeatures(e.point, { layers: ['hotspot-points', 'hotspot-clusters'] })
        if (points.length === 0) onSelectRef.current(null)
      })
      map.on('mousemove', 'hotspot-points', (e) => {
        map.getCanvas().style.cursor = 'pointer'
        const f = e.features?.[0]
        const p = f?.properties
        if (!p || f?.geometry.type !== 'Point') return
        const coords = (f.geometry as { coordinates: [number, number] }).coordinates
        popupRef.current?.remove()
        popupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 13, className: 'vestigium-popup' })
          .setLngLat(coords).setText(`${p.sensor} · ${p.date_utc} UTC · ${Number(p.frp_mw).toFixed(1)} MW`).addTo(map)
      })
      map.on('mouseleave', 'hotspot-points', () => { map.getCanvas().style.cursor = ''; popupRef.current?.remove() })
      map.on('mouseenter', 'hotspot-clusters', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'hotspot-clusters', () => { map.getCanvas().style.cursor = '' })
      setReady(true)
      publishBounds()
    })
    map.on('moveend', publishBounds)
    return () => { popupRef.current?.remove(); map.remove(); mapRef.current = null }
  }, [])

  useEffect(() => {
    if (!ready || !mapRef.current) return
    const source = mapRef.current.getSource('hotspots') as GeoJSONSource | undefined
    if (source && detections) source.setData(detections as Parameters<GeoJSONSource['setData']>[0])
  }, [detections, ready])

  useEffect(() => {
    if (!ready || !mapRef.current || focusedId === null) return
    const record = recordsRef.current?.features.find(r => String(r.properties.id) === String(focusedId))
    if (record) mapRef.current.easeTo({ center: record.geometry.coordinates, zoom: Math.max(mapRef.current.getZoom(), 7.5), duration: 650 })
  }, [focusedId, ready])

  return <div className="map-root">
    <div ref={containerRef} className="map-canvas" aria-label="Interactive Indonesia hotspot map" role="application"/>
    <div className="map-vignette" />
    <div className="map-compass"><Crosshair size={15} strokeWidth={1.5}/> 117° E / 02° S</div>
    <div className="map-zoom"><button aria-label="Zoom in" onClick={() => mapRef.current?.zoomIn()}><ZoomIn size={19}/></button><button aria-label="Zoom out" onClick={() => mapRef.current?.zoomOut()}><ZoomOut size={19}/></button></div>
    <div className="map-scale-hint">BASEMAP © OPENSTREETMAP / © CARTO</div>
  </div>
}
