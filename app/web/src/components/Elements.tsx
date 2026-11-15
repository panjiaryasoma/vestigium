import { ArrowUpRight, AlertTriangle } from 'lucide-react'
import type { ReactNode } from 'react'
import type { Meta } from '../lib/types'

export function Eyebrow({ index, children }: { index?: string; children: ReactNode }) {
  return <div className="eyebrow">{index && <span className="eyebrow-index">{index} /</span>}{children}</div>
}
export function DataNotice({ meta, concise = false }: { meta: Meta | null; concise?: boolean }) {
  if (!meta) return <div className="data-notice"><AlertTriangle size={14}/> API unavailable. Start the FastAPI server to view data.</div>
  return <div className={`data-notice ${meta.synthetic ? 'notice-synthetic' : 'notice-live'}`}><AlertTriangle size={14}/>
    {meta.synthetic ? (concise ? 'SYNTHETIC DEMO DATA · NOT NASA OBSERVATIONS' : meta.message)
    : meta.mode === 'archive' ? (concise ? 'NASA FIRMS · GENUINE COORDINATES · SAMPLED MAP' : meta.message)
    : meta.mode === 'unavailable' ? 'DATA UNAVAILABLE · NO POINTS DISPLAYED'
    : 'NASA FIRMS PIXEL DETECTIONS · NOT DISTINCT FIRE EVENTS'}
  </div>
}
export function PageTitle({ index, label, title, description }: { index: string; label: string; title: ReactNode; description: string }) {
  return <div className="page-heading">
    <Eyebrow index={index}>{label}</Eyebrow>
    <div className="heading-content"><h1>{title}</h1><p>{description}</p></div>
  </div>
}
export function ExternalReference({ href, children }: { href: string; children: ReactNode }) {
  return <a className="external-ref" href={href} target="_blank" rel="noreferrer">{children}<ArrowUpRight size={17}/></a>
}
