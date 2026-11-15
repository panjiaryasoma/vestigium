import { Link, NavLink } from 'react-router-dom'
import { ArrowUpRight, Menu, X } from 'lucide-react'
import { useState } from 'react'
import type { Meta } from '../lib/types'

const nav = [
  ['Explore', '/explore'], ['Archive', '/archive'], ['Analysis', '/analysis'], ['Impact', '/impact'], ['Method', '/methodology'],
]

export function Brand({ small = false }: { small?: boolean }) {
  return <Link className={`brand ${small ? 'brand-small' : ''}`} to="/" aria-label="VESTIGIUM, home">
    <span className="brand-mark">V<span className="brand-dot">.</span></span>
    <span className="brand-word">VESTIGIUM<span className="brand-dot">.</span></span>
  </Link>
}

export function Header({ mode }: { mode?: Meta['mode'] }) {
  const [expanded, setExpanded] = useState(false)
  return <header className="site-header">
    <div className="header-identity"><Brand small /><span className="header-kicker">EARTH OBSERVATION<br /> / INVESTIGATIVE ATLAS</span></div>
    <button className="menu-toggle" onClick={() => setExpanded(!expanded)} aria-label="Toggle navigation" aria-expanded={expanded}>{expanded ? <X size={21}/> : <Menu size={21}/>}</button>
    <nav className={`site-nav ${expanded ? 'expanded' : ''}`} aria-label="Primary navigation">
      {nav.map(([label, path]) => <NavLink key={path} to={path} onClick={() => setExpanded(false)} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{label}</NavLink>)}
    </nav>
    <div className="header-edge"><span className="header-status"><i className={mode === 'live' ? 'status-dot online' : 'status-dot'}/> {mode === 'live' ? 'DATA CONNECTED' : 'DEMO ENVIRONMENT'}</span><Link to="/explore" className="header-enter" aria-label="Open archive"><ArrowUpRight size={17}/></Link></div>
  </header>
}

export function Footer() {
  return <footer className="footer"><span>VESTIGIUM / GA TIDUR</span><span>NASA SPACE APPS CHALLENGE 2026</span><span>EARTH REMEMBERS WHAT FIRE LEAVES BEHIND.</span></footer>
}
