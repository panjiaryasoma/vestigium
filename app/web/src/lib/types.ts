export type Sensor = 'ALL' | 'MODIS' | 'VIIRS_SNPP' | 'VIIRS_NOAA20'

export interface Meta {
  product: string
  mode: 'demo' | 'live'
  synthetic: boolean
  years: number[]
  sensors: string[]
  regions: string[]
  has_harmonization_calendar: boolean
  message: string
  time_zone: string
  observation_unit: string
  viewport_note: string
}

export interface HotspotProperties {
  id: string | number
  timestamp_utc: string | null
  date_utc: string
  sensor: string
  satellite: string | null
  frp_mw: number
  confidence_modis_pct: number | null
  confidence_viirs_label: string | null
  province?: string | null
  synthetic: boolean
}

export interface HotspotFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: HotspotProperties
}

export interface HotspotCollection {
  type: 'FeatureCollection'
  features: HotspotFeature[]
  meta: { returned: number; limit: number; truncated: boolean; synthetic: boolean; sampled: boolean; note: string }
}

export interface TemporalRow { year: number; month: number | null; count: number; date: string }
export interface TemporalResponse { grain: string; sensor: string; year: number | null; data: TemporalRow[]; synthetic: boolean; warning: string }
export interface CalendarRow { year: number; month: number; MODIS: number | null; VIIRS_SNPP: number | null; VIIRS_NOAA20: number | null; calendar_display_estimate: number | null; calendar_method: string }
export interface CalendarResponse { available: boolean; year: number; data: CalendarRow[]; synthetic: boolean; warning: string }
export interface AnalysisFinding { month: number; count: number; baseline_median: number; deviation_score: number; classification: string }
export interface AnalysisResponse { year: number; findings: AnalysisFinding[]; synthetic: boolean; method: string; warning: string }
export interface EvaluationResponse { kind: string; as_of: string; test_period: string; test_grid_months: number; reference: string; metrics: Array<{ method: string; mae: number; rmse: number; spearman: number }>; source: string; warning: string }
