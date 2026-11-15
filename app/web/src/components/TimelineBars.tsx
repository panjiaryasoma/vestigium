import { MONTH_NAMES, numberFormat } from '../lib/api'
import type { TemporalRow } from '../lib/types'

export function TimelineBars({ rows, selected, onSelect }: { rows: TemporalRow[]; selected: number; onSelect: (month: number) => void }) {
  const counts = Array.from({ length: 12 }, (_, index) => rows.find(r => r.month === index + 1)?.count || 0)
  const peak = Math.max(...counts, 1)
  return <div className="timeline-chart" role="group" aria-label="Select month from raw detection counts">
    {counts.map((count, index) => <button key={index} onClick={() => onSelect(index + 1)}
      title={`${MONTH_NAMES[index]}: ${numberFormat(count)} detected pixels${index + 1 === selected ? ' (selected)' : ''}`}
      className={`timeline-column ${index + 1 === selected ? 'is-selected' : ''}`} aria-pressed={index + 1 === selected}>
      <span className="timeline-bar-rail"><i style={{ height: `${Math.max(5, count / peak * 100)}%` }} /></span>
      <span className="timeline-bar-label">{MONTH_NAMES[index].toUpperCase()}</span>
    </button>)}
  </div>
}
