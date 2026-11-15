import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, CalendarDays, Info } from 'lucide-react'
import { PageTitle, DataNotice, Eyebrow } from '../components/Elements'
import { getJson, MONTH_NAMES, numberFormat, sensorLabel } from '../lib/api'
import type { CalendarResponse, Meta, Sensor, TemporalResponse } from '../lib/types'

export default function Archive({ meta }: { meta: Meta | null }) {
  const [sensor, setSensor] = useState<Sensor>('ALL')
  const [year, setYear] = useState(2015)
  const [data, setData] = useState<TemporalResponse | null>(null)
  const [calendar, setCalendar] = useState<CalendarResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    const ctrl = new AbortController()
    setError(false)
    getJson<TemporalResponse>('/api/v1/temporal', { sensor, grain: 'monthly' }, ctrl.signal).then(setData).catch(e => { if (e.name !== 'AbortError') setError(true) })
    return () => ctrl.abort()
  }, [sensor])
  useEffect(() => {
    const ctrl = new AbortController()
    getJson<CalendarResponse>('/api/v1/calendar', { year }, ctrl.signal).then(setCalendar).catch(() => setCalendar(null))
    return () => ctrl.abort()
  }, [year])

  const counts = useMemo(() => {
    const records = new Map<string, number>()
    data?.data.forEach(r => { if (r.month != null) records.set(`${r.year}-${r.month}`, r.count) })
    return records
  }, [data])
  const isAvailable = (y: number, m: number) => !(y === 2000 && m < 11) && !(sensor === 'VIIRS_SNPP' && y < 2012) && !(sensor === 'VIIRS_NOAA20' && y < 2018)
  const max = Math.max(1, ...Array.from(counts.values()))
  const annual = (meta?.years || Array.from({ length: 26 }, (_, i) => 2000 + i)).map(y => ({ year: y, count: Array.from({ length: 12 }, (_, i) => counts.get(`${y}-${i + 1}`) || 0).reduce((a, b) => a + b, 0) }))
  const maxAnnual = Math.max(...annual.map(r => r.count), 1)
  const total = annual.reduce((sum, record) => sum + record.count, 0)

  return <main className="inner-page archive-page">
    <PageTitle index="02" label="TIME AS EVIDENCE" title={<>THE FIRE <i>ARCHIVE.</i></>}
      description="Twenty-six calendar years of satellite detection records. Examine the seasonal signal without mistaking pixels for separate fires."/>
    <DataNotice meta={meta} concise/>
    <div className="archive-overview"><div><span>OBSERVATION WINDOW</span><strong>2000 <i>—</i> 2025</strong></div><div><span>DISPLAYED RAW PIXEL DETECTIONS</span><strong>{data ? numberFormat(total) : '—'}</strong></div><div><span>REFERENCE SYSTEM</span><strong>UTC / FIRMS</strong></div></div>
    <section className="archive-panel">
      <div className="section-top"><div><Eyebrow index="01">MONTH-BY-MONTH / 2000–2025</Eyebrow><h2>THE TEMPORAL GRID<span>.</span></h2></div><label className="form-select-dark">SOURCE <select value={sensor} onChange={e => setSensor(e.target.value as Sensor)}>{(['ALL', 'MODIS', 'VIIRS_SNPP', 'VIIRS_NOAA20'] as Sensor[]).map(s => <option key={s} value={s}>{sensorLabel(s)}</option>)}</select></label></div>
      {error ? <p className="empty-state">The API is unavailable. Start the backend and reload this page.</p> : <div className="heatmap-wrap"><div className="heatmap">
        <div className="heatmap-month-head"><div/><span>J</span><span>F</span><span>M</span><span>A</span><span>M</span><span>J</span><span>J</span><span>A</span><span>S</span><span>O</span><span>N</span><span>D</span></div>
        {annual.map(({ year: y }) => <div className="heatmap-row" key={y}><span className="heatmap-year">{y}</span>
          {Array.from({ length: 12 }, (_, i) => {
            const count = counts.get(`${y}-${i + 1}`) || 0
            const available = isAvailable(y, i + 1)
            const intensity = count ? Math.max(.10, Math.log1p(count) / Math.log1p(max)) : 0
            return <Link to={`/explore?year=${y}&month=${i + 1}`} key={i} className={`heatmap-cell ${count ? 'has-observations' : ''} ${!available ? 'not-observed' : ''}`}
              style={{ backgroundColor: count ? `rgba(211,72,58,${intensity.toFixed(3)})` : undefined }}
              title={available ? `${MONTH_NAMES[i]} ${y}: ${numberFormat(count)} raw detected pixels. Open map.` : `${MONTH_NAMES[i]} ${y}: no sensor coverage in the archived dataset`} aria-label={available ? `View ${MONTH_NAMES[i]} ${y}: ${numberFormat(count)} detections` : `${MONTH_NAMES[i]} ${y}: no data`}  />
          })}</div>)}
        </div><div className="heatmap-key"><span>FEWER DETECTIONS</span><div className="heatmap-gradient"/><span>MORE DETECTIONS</span></div></div>}
      <div className="archive-footnote"><Info size={15}/> Colors represent raw pixel detection counts within each selected sensor. Sensor availability changes by year; cross-sensor totals are not harmonized.</div>
    </section>

    <section className="archive-panel yearly-section"><div className="section-top"><div><Eyebrow index="02">YEARLY COUNTS / RAW SERIES</Eyebrow><h2>ANNUAL FOOTPRINT<span>.</span></h2></div><span className="micro-caption">SELECT A YEAR TO INVESTIGATE</span></div>
      <div className="annual-chart">{annual.map(({ year: y, count }) => <button key={y} onClick={() => setYear(y)} title={`${y}: ${numberFormat(count)} raw detected pixels`} aria-label={`Select ${y} for calendar comparison`}
        className={`annual-column ${y === year ? 'selected-year' : ''}`}><span className="annual-track"><i style={{ height: `${Math.max(2, count / maxAnnual * 100)}%` }}/></span><span className="annual-year">{String(y).slice(-2)}</span></button>)}</div>
      <div className="annual-selected"><CalendarDays size={18}/><span>SELECTED / {year}</span><strong>{numberFormat(annual.find(r => r.year === year)?.count)}</strong><Link to={`/explore?year=${year}&month=9`}>OPEN MAP <ArrowUpRight size={14}/></Link></div>
    </section>

    <section className="calendar-section"><div><Eyebrow index="03">INSTRUMENT HANDOFF / 2012</Eyebrow><h2>CAN TWO SATELLITES<br/>TELL <i>ONE STORY?</i></h2><p>MODIS and VIIRS do not see the same number of thermal pixels. The harmonization experiment models a VIIRS S-NPP-like detection-count proxy for MODIS-positive grid-months.</p>
      <Link className="inline-red-link" to="/analysis">REVIEW MODEL EVIDENCE <ArrowUpRight size={18}/></Link></div>
      <div className="calibration-panel"><div className="calibration-panel-head">CALIBRATION STATUS / {year}<span>{calendar?.available ? 'ARTIFACT CONNECTED' : 'NO ARTIFACT MOUNTED'}</span></div>
        {calendar?.available ? <><div className="calibration-grid">{calendar.data.map(r => <div key={r.month} className="calibration-month"><small>{MONTH_NAMES[r.month - 1]}</small><strong>{numberFormat(r.calendar_display_estimate)}</strong><span>{r.calendar_method === "observed_viirs_snpp" ? "OBSERVED S-NPP" : "MODELED PROXY"}</span></div>)}</div><p className="calibration-warning">{calendar.warning}</p></>
          : <div className="calibration-empty"><strong>NOT AVAILABLE<span>.</span></strong><p>{calendar?.warning || 'Attach the harmonized_calendar_monthly.csv pipeline output to enable the experimental calibration calendar. No synthetic calibration is invented.'}</p></div>}
      </div>
    </section>
  </main>
}
