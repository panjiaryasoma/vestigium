import { ArrowUpRight, BookOpen, LockKeyhole } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Eyebrow } from '../components/Elements'

export default function Impact() {
  return <main className="impact-page">
    <div className="impact-hero"><div className="impact-kicker"><Eyebrow index="04">THE AFTERMATH / INVESTIGATIVE STORIES</Eyebrow><span>RESEARCH MODULE / PLANNED</span></div>
      <div className="impact-hero-inner"><h1>THE FLAMES<br/>FADE. <i>THE<br/>LAND REMAINS.</i></h1><p>What happened to the places once detected burning? Forest recovery, plantations, industrial development, or something else? This is the next investigation, not a conclusion we can claim today.</p></div>
      <div className="impact-lines"><span>00 / INCIDENT</span><span>01 / ONE YEAR LATER</span><span>05 / FIVE YEARS LATER</span><span>24 / TWENTY-FOUR YEARS LATER</span></div>
    </div>
    <section className="impact-process"><div><Eyebrow index="01">A PROPOSED INVESTIGATIVE PATH</Eyebrow><h2>FOLLOW THE<br/><i>TRANSFORMATION.</i></h2></div><div className="impact-steps"><div><span>01</span><h3>Detect the event</h3><p>Locate a historical satellite hotspot, then corroborate actual burned area independently.</p></div><div><span>02</span><h3>Build the timeline</h3><p>Compare land-cover maps and remotely sensed imagery before and after the event.</p></div><div><span>03</span><h3>Check the evidence</h3><p>Interpret land-cover classification uncertainty and avoid assigning motives or responsibility.</p></div></div></section>
    <section className="impact-status"><div><LockKeyhole size={28}/><span>UNVERIFIED FEATURE / NOT YET LIVE</span></div><h2>NO CONCLUSIONS<br/>WITHOUT <i>EVIDENCE.</i></h2><p>Post-fire land transitions require independently validated MapBiomas FIRE / LANDY and Landsat imagery. This module is an editorial research plan; the app does not fabricate 1–24-year land-cover outcomes.</p><div className="impact-links"><a href="https://landy.mapbiomas.id/" target="_blank" rel="noreferrer"><BookOpen size={17}/> MAPBIOMAS LANDY <ArrowUpRight size={15}/></a><Link to="/methodology">METHODOLOGY <ArrowUpRight size={15}/></Link></div></section>
  </main>
}
