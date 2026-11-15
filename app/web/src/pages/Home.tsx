import { Link } from 'react-router-dom'
import { ArrowDown, ArrowRight, ArrowUpRight, Crosshair, Layers3, ScanSearch, Waves } from 'lucide-react'
import { Eyebrow } from '../components/Elements'
import { MapArtwork } from '../components/MapArtwork'
import { Footer } from '../components/Brand'

export default function Home() {
  return <main className="landing">
    <section className="hero" aria-labelledby="hero-headline">
      <MapArtwork />
      <div className="hero-topline"><span>GA TIDUR / EARTH OBSERVATION</span><span>ARCHIVE NO. 001<br/>INDONESIA / 2000—2025</span></div>
      <div className="hero-content">
        <div className="hero-intro"><span className="red-asterisk">✳</span> A RECORD OF WHAT REMAINS</div>
        <h1 id="hero-headline">THE EARTH<br/>KEEPS <em>RECEIPTS.</em></h1>
        <div className="hero-bottom"><p>26 years of satellite-observed fire activity.<br/>One atlas to question the patterns beneath the surface.</p>
          <Link to="/explore" className="primary-action">ENTER THE ARCHIVE <ArrowUpRight size={19}/></Link>
        </div>
      </div>
      <div className="hero-foot"><span><ArrowDown size={16}/> SCROLL TO INVESTIGATE</span><span>01 — 04 / BEGIN HERE</span><span>NASA SPACE APPS CHALLENGE 2026</span></div>
    </section>

    <section className="mission-section" id="about">
      <div className="mission-side"><Eyebrow index="01">THE QUESTION</Eyebrow><div className="mission-coordinates">6°N TO 11°S<br/>95°E TO 141°E</div></div>
      <div className="mission-body"><h2>EVERY POINT<br/>LEAVES A <span>TRAIL.</span></h2><p>Fire is visible from space. Its history is harder to read. Different satellites observe the same planet with different sensitivities. VESTIGIUM brings detections, time, and evidence into an investigative frame.</p>
        <div className="mission-link"><Link to="/methodology">READ THE METHODOLOGY <ArrowUpRight size={18}/></Link></div>
      </div>
      <div className="mission-rule"/>
    </section>

    <section className="features-section">
      <div className="features-header"><Eyebrow index="02">EXPLORE THE SYSTEM</Eyebrow><span>FOUR WAYS TO FOLLOW THE EVIDENCE</span></div>
      <div className="feature-grid">
        {[
          { no: '01', name: 'THE ATLAS', desc: 'Pinpoint satellite thermal detections by place, sensor, and date.', to: '/explore', icon: <Crosshair size={24}/> },
          { no: '02', name: 'THE ARCHIVE', desc: 'Trace monthly and yearly records across the observed period.', to: '/archive', icon: <Layers3 size={24}/> },
          { no: '03', name: 'THE ANALYSIS', desc: 'Question anomalies, calibration results, and their limits.', to: '/analysis', icon: <ScanSearch size={24}/> },
          { no: '04', name: 'THE AFTERMATH', desc: 'A framework for investigating what changes after the flames.', to: '/impact', icon: <Waves size={24}/> },
        ].map(f => <Link className="feature-entry" key={f.no} to={f.to}><div className="feature-top"><span>{f.no} / FIELD</span>{f.icon}</div><div className="feature-bottom"><h3>{f.name}</h3><p>{f.desc}</p><ArrowRight className="feature-arrow" size={22}/></div></Link>)}
      </div>
    </section>
    <section className="closing-cta"><div className="closing-no">03 / OPEN SOURCE OF EVIDENCE</div><div><p>DON'T JUST COUNT THE FIRES.</p><h2>READ BETWEEN<br/>THE <i>POINTS.</i></h2></div><Link to="/explore" className="closing-link">EXPLORE THE ATLAS <ArrowUpRight size={28}/></Link></section>
    <Footer/>
  </main>
}
