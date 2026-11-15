import { useEffect, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, AlertTriangle, ScanSearch } from 'lucide-react'
import { DataNotice, Eyebrow, ExternalReference, PageTitle } from '../components/Elements'
import { FULL_MONTH_NAMES, getJson, numberFormat } from '../lib/api'
import type { AnalysisResponse, EvaluationResponse, Meta } from '../lib/types'

export default function Analysis({ meta }: { meta: Meta | null }) {
  const [year, setYear] = useState(2015)
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null)
  useEffect(() => {
    const ctrl = new AbortController()
    getJson<AnalysisResponse>('/api/v1/analysis', { year }, ctrl.signal).then(setAnalysis).catch(() => setAnalysis(null))
    return () => ctrl.abort()
  }, [year])
  useEffect(() => { getJson<EvaluationResponse>('/api/v1/evaluation').then(setEvaluation).catch(() => setEvaluation(null)) }, [])
  const highlight = analysis?.findings[0]
  const metrics = evaluation?.metrics || []
  const maxMae = Math.max(1, ...metrics.map(m => m.mae))
  const maxRmse = Math.max(1, ...metrics.map(m => m.rmse))

  return <main className="inner-page analysis-page">
    <PageTitle index="03" label="EXAMINE / DON'T ASSUME" title={<>PATTERNS ARE<br/><i>NOT VERDICTS.</i></>} description="Anomalies can suggest questions. They cannot reveal whether a fire was intentional. Here, methods, evidence, and uncertainty remain visible."/>
    <DataNotice meta={meta} concise/>
    <div className="analysis-intro"><div className="analysis-big-number">01<span>/03</span></div><div><Eyebrow>THE CORE RESEARCH PROBLEM</Eyebrow><p>Different eyes in orbit, different counts on Earth. Before explaining a pattern, first ask whether the pattern is partly a product of the instrument observing it.</p></div><ScanSearch size={68} strokeWidth={.75}/></div>

    <section className="analysis-lab"><div className="section-top"><div><Eyebrow index="01">ARCHIVED MODEL EVALUATION</Eyebrow><h2>THE CALIBRATION TEST<span>.</span></h2></div><div className="lab-aside">HOLDOUT / 2023—2025<br/>{numberFormat(evaluation?.test_grid_months)} GRID-MONTHS</div></div>
      <p className="lab-description">Historical reported experiment: MODIS-positive 25 km equal-area grid-months, with VIIRS S-NPP as reference. These are archived values, <strong>not a fresh model training run or live API inference.</strong></p>
      <div className="metrics-duo"><div className="metric-graph"><div className="metric-graph-header"><span>01 / MEAN ABSOLUTE ERROR</span><b>LOWER IS BETTER <ArrowDownRight size={15}/></b></div>{metrics.map(r => <div key={r.method} className="metric-row"><span>{r.method}</span><div><i style={{ width: `${r.mae / maxMae * 100}%` }} className={r.method === 'Poisson ML' ? 'metric-highlight' : ''}/></div><strong>{r.mae.toFixed(2)}</strong></div>)}</div>
        <div className="metric-graph"><div className="metric-graph-header"><span>02 / ROOT MEAN SQUARED ERROR</span><b>LOWER IS BETTER <ArrowDownRight size={15}/></b></div>{metrics.map(r => <div key={r.method} className="metric-row"><span>{r.method}</span><div><i style={{ width: `${r.rmse / maxRmse * 100}%` }} className={r.method === 'Global scaling' ? 'metric-highlight' : ''}/></div><strong>{r.rmse.toFixed(2)}</strong></div>)}</div></div>
      <div className="metric-conclusion"><span>WHAT THE RESULTS ACTUALLY SHOW</span><p>Poisson ML has the lowest archived test MAE (10.24). Global scaling has the lowest RMSE (21.87). Neither justifies inventing missing detections or attributing ignition causes.</p></div>
      <p className="lab-provenance">Source: <a href="https://github.com/panjiaryasoma/vestigium/blob/main/docs/harmonization/evidence/archived_metrics_2026-11-15.json" target="_blank" rel="noreferrer">Archived evaluation evidence <ArrowUpRight size={12}/></a>. Full original-source reconstruction is pending independent confirmation.</p>
    </section>

    <section className="anomaly-section"><div className="anomaly-heading"><div><Eyebrow index="02">EXPLORATORY SIGNAL SCAN</Eyebrow><h2>OUTSIDE THE<br/><i>EXPECTED RANGE.</i></h2></div><label className="form-select-dark">INSPECT YEAR <select value={year} onChange={e => setYear(Number(e.target.value))}>{Array.from({ length: 26 }, (_, i) => 2000 + i).map(y => <option key={y}>{y}</option>)}</select></label></div>
      <div className="anomaly-layout"><div className="anomaly-feature"><span className="feature-number">HIGHEST MONTHLY DEVIATION / {year}</span><strong>{highlight ? FULL_MONTH_NAMES[highlight.month - 1].toUpperCase() : 'NO DATA'}</strong><div className="score-line">ROBUST DEVIATION SCORE <b>{highlight?.deviation_score.toFixed(2) ?? '—'}</b></div><p>{highlight ? `${numberFormat(highlight.count)} raw satellite pixel detections versus ${numberFormat(highlight.baseline_median)} for the historical median of that calendar month.` : 'Start the API to run exploratory detection comparison.'}</p><div className="anomaly-caveat"><AlertTriangle size={16}/> {meta?.synthetic ? 'THIS IS A SYNTHETIC DEMONSTRATION, NOT A REAL ANOMALY.' : 'SENSOR CHANGES MAY INFLATE CROSS-YEAR DEVIATIONS.'}</div></div>
        <div className="anomaly-table"><div className="anomaly-table-header"><span>MONTH / UTC</span><span>RAW DETECTIONS</span><span>ROBUST SCORE</span></div>{analysis?.findings.slice(0, 6).map(f => <div className="anomaly-table-row" key={f.month}><span>{FULL_MONTH_NAMES[f.month - 1]}</span><strong>{numberFormat(f.count)}</strong><b>{f.deviation_score > 0 ? '+' : ''}{f.deviation_score.toFixed(2)}</b></div>)}<p>{analysis?.method || 'Statistical scan unavailable. Connect API.'}</p></div></div>
    </section>

    <section className="analysis-boundaries"><Eyebrow index="03">EVIDENCE BOUNDARIES</Eyebrow><h2>WHAT THE DATA<br/><i>CANNOT TELL US.</i></h2><div className="boundary-grid"><div><span>01 / CAUSE</span><h3>Intentional or natural?</h3><p>Satellite thermal anomalies cannot establish arson or natural ignition. Cause requires verified ground evidence, weather, lightning, and investigative context.</p></div><div><span>02 / EXTENT</span><h3>How much burned?</h3><p>A hotspot pixel is not burned-area measurement. Independent burned-area products and land-cover data are necessary for that question.</p></div><div><span>03 / CONSISTENCY</span><h3>One continuous record?</h3><p>Changing instruments, overpass windows, cloud cover, and an explicit 2012 model-to-observation handoff limit historical comparisons.</p></div></div><ExternalReference href="https://firms.modaps.eosdis.nasa.gov/">NASA FIRMS / SOURCE REFERENCE</ExternalReference></section>
  </main>
}
