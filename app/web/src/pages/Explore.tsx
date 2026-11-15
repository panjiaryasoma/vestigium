import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowUpRight, ChevronDown, Crosshair, Database, Info, MapPin, SlidersHorizontal, X } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import HotspotMap from '../components/HotspotMap'
import { TimelineBars } from '../components/TimelineBars'
import { DataNotice, Eyebrow } from '../components/Elements'
import { FULL_MONTH_NAMES, getJson, numberFormat, sensorLabel } from '../lib/api'
import type { HotspotCollection, HotspotFeature, Meta, Sensor, TemporalResponse } from '../lib/types'

export default function Explore({ meta }: { meta: Meta | null }) {
  const [params, setParams] = useSearchParams()
  const initialYear = Number(params.get('year') || 2015)
  const initialMonth = Number(params.get('month') || 9)
  const [year, setYear] = useState(initialYear >= 2000 && initialYear <= 2025 ? initialYear : 2015)
  const [month, setMonth] = useState(initialMonth >= 1 && initialMonth <= 12 ? initialMonth : 9)
  const [sensor, setSensor] = useState<Sensor>('ALL')
  const [region, setRegion] = useState('')
  const [bbox, setBbox] = useState('94,-12,142,7')
  const [records, setRecords] = useState<HotspotCollection | null>(null)
  const [selected, setSelected] = useState<HotspotFeature | null>(null)
  const [temporal, setTemporal] = useState<TemporalResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [mapError, setMapError] = useState('')
  const [controlsOpen, setControlsOpen] = useState(false)

  useEffect(() => {
    setParams({ year: String(year), month: String(month) }, { replace: true })
  }, [year, month, setParams])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setMapError('')
    getJson<HotspotCollection>('/api/v1/hotspots', { year, month, sensor, region, bbox, limit: 1800 }, controller.signal)
      .then((res) => { setRecords(res); setSelected(null) })
      .catch(err => { if (err.name !== 'AbortError') { setRecords(null); setMapError('Could not load hotspot records. Make sure the API is running.') } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [year, month, sensor, region, bbox])

  useEffect(() => {
    const controller = new AbortController()
    getJson<TemporalResponse>('/api/v1/temporal', { year, sensor }, controller.signal).then(setTemporal).catch(() => setTemporal(null))
    return () => controller.abort()
  }, [year, sensor])

  const onViewport = useCallback((next: string) => setBbox(old => old === next ? old : next), [])
  const selectedLocation = selected?.geometry.coordinates
  const selectedProps = selected?.properties
  const annualCount = useMemo(() => temporal?.data.reduce((sum, item) => sum + item.count, 0) || 0, [temporal])
  const monthCount = temporal?.data.find(d => d.month === month)?.count || 0
  const years = meta?.years || Array.from({ length: 26 }, (_, i) => 2000 + i)

  return <main className="explore-page">
    <div className="explore-header"><div><Eyebrow index="01">THE CARTOGRAPHIC ARCHIVE</Eyebrow><h1>THE FIRE <i>ATLAS.</i></h1></div><div className="explore-header-aside"><span>INDONESIA</span><span>2000 → 2025</span><span>NASA FIRMS · UTC</span></div></div>
    <DataNotice meta={meta} concise />

    <div className="atlas-layout">
      <div className="atlas-primary">
        <div className="map-stage">
          <HotspotMap detections={records} onSelect={setSelected} onViewport={onViewport} focusedId={selectedProps?.id ?? null}/>
          <div className="map-stage-top"><div className="map-title"><span>01 / HISTORICAL MAP EXPLORER</span><strong>{year} <span>/</span> {FULL_MONTH_NAMES[month - 1].toUpperCase()}</strong></div><div className="map-live"><span className="map-live-point"/> {loading ? 'FETCHING' : 'VIEWPORT READY'}</div></div>
          <button className="filter-mobile-toggle" onClick={() => setControlsOpen(!controlsOpen)}><SlidersHorizontal size={17}/> FILTER RECORDS <ChevronDown size={15}/></button>
          <div className={`map-filters ${controlsOpen ? 'map-filters-open' : ''}`}>
            <label>YEAR<select aria-label="Year" value={year} onChange={e => setYear(Number(e.target.value))}>{years.map(y => <option key={y} value={y}>{y}</option>)}</select></label>
            <label>MONTH<select aria-label="Month" value={month} onChange={e => setMonth(Number(e.target.value))}>{FULL_MONTH_NAMES.map((name, index) => <option key={name} value={index + 1}>{name}</option>)}</select></label>
            <label>SENSOR<select aria-label="Sensor" value={sensor} onChange={e => setSensor(e.target.value as Sensor)}>{(['ALL', 'MODIS', 'VIIRS_SNPP', 'VIIRS_NOAA20'] as Sensor[]).map(s => <option key={s} value={s}>{sensorLabel(s)}</option>)}</select></label>
            <label>REGION<select aria-label="Region" value={region} onChange={e => setRegion(e.target.value)}><option value="">All regions</option>{(meta?.regions || []).map(r => <option key={r}>{r}</option>)}</select></label>
          </div>
          {mapError && <div className="map-error"><Info size={16}/>{mapError}</div>}
          <div className="map-stage-bottom"><div className="map-legend"><span className="legend-hotspot"/> SATELLITE DETECTION <span className="legend-separator"/> CIRCLES ARE CLUSTERED POINTS</div><span>{numberFormat(records?.meta.returned)} / VIEWPORT</span></div>
        </div>
        <div className="atlas-timeline"><div className="timeline-title"><div><span>02 / TEMPORAL RECORD</span><h3>ACTIVITY TIMELINE <small>RAW DETECTIONS</small></h3></div><div className="timeline-metrics"><span>YEAR TOTAL <b>{numberFormat(annualCount)}</b></span><span>SELECTED MONTH <b>{numberFormat(monthCount)}</b></span></div></div>
          <TimelineBars rows={temporal?.data || []} selected={month} onSelect={setMonth}/>
          <div className="timeline-caption">Monthly pixel detections, all Indonesian regions. Bars are not counts of separate fires.</div>
        </div>
      </div>
      <aside className="evidence-panel">
        {selected && selectedProps && selectedLocation ? <>
          <div className="evidence-head"><Eyebrow index="03">EVIDENCE RECORD</Eyebrow><button aria-label="Close selected record" onClick={() => setSelected(null)}><X size={18}/></button></div>
          <div className="record-index">OBSERVATION / {String(selectedProps.id).slice(-10)}</div>
          <h2>THERMAL<br/>DETECTION<span>.</span></h2>
          <div className="record-alert"><span className="record-red-dot"/> DETECTED HOTSPOT PIXEL</div>
          <div className="record-rows">
            <div><span>DATE / UTC</span><strong>{selectedProps.date_utc}</strong></div>
            <div><span>TIME / UTC</span><strong>{selectedProps.timestamp_utc?.slice(11, 16) || 'Unavailable'}</strong></div>
            <div><span>INSTRUMENT</span><strong>{sensorLabel(selectedProps.sensor)}</strong></div>
            <div><span>FRP / MW</span><strong>{selectedProps.frp_mw?.toFixed(1) ?? '—'}</strong></div>
            <div><span>LATITUDE</span><strong>{selectedLocation[1].toFixed(5)}</strong></div>
            <div><span>LONGITUDE</span><strong>{selectedLocation[0].toFixed(5)}</strong></div>
            <div><span>CONFIDENCE</span><strong>{selectedProps.confidence_modis_pct != null ? `${selectedProps.confidence_modis_pct}% · MODIS` : selectedProps.confidence_viirs_label ? `${selectedProps.confidence_viirs_label.toUpperCase()} · VIIRS CLASS` : 'Unreported'}</strong></div>
            {selectedProps.province && <div><span>DEMO LOCATION LABEL</span><strong>{selectedProps.province}</strong></div>}
          </div>
          <p className="record-disclaimer">A thermal pixel observation does not establish fire cause, burned area, or a distinct wildfire. {selectedProps.synthetic ? 'This record is SYNTHETIC.' : 'Source: NASA FIRMS.'}</p>
        </> : <>
          <div className="evidence-head"><Eyebrow index="03">FIELD NOTES</Eyebrow><Crosshair size={19}/></div>
          <div className="aside-supergraphic">{year}<span>.</span></div>
          <h2>READ THE<br/>LANDSCAPE<span>.</span></h2>
          <p className="evidence-intro">Select a red point to inspect its date, instrument, radiant power and exact coordinates.</p>
          <div className="aside-stat"><span>VISIBLE DETECTIONS</span><strong>{numberFormat(records?.meta.returned)}</strong><small>Current map viewport · {FULL_MONTH_NAMES[month - 1]} {year}</small></div>
          <div className="aside-stat"><span>ACTIVE SENSOR FILTER</span><strong className="aside-stat-sensor">{sensorLabel(sensor)}</strong></div>
          <div className="aside-note"><MapPin size={18}/><p>Pan the map or zoom in to retrieve detections for the visible geographic area.</p></div>
          <Link className="aside-link" to="/analysis">EXAMINE THE EVIDENCE <ArrowUpRight size={18}/></Link>
        </>}
        {records?.meta.truncated && <div className="truncation"><Database size={15}/> Viewport limit reached. Zoom in to inspect more points; visible count is not exhaustive.</div>}
      </aside>
    </div>
    <div className="atlas-bottom-note"><span><Info size={15}/> REGIONS ARE GEOGRAPHIC BOUNDS, NOT ADMINISTRATIVE PROVINCE BORDERS.</span><span>DATA PROVENANCE <Link to="/methodology">VIEW METHOD <ArrowUpRight size={13}/></Link></span></div>
  </main>
}
