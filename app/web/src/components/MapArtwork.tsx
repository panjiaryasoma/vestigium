export function MapArtwork() {
  return <div className="hero-artwork" aria-hidden="true">
    <svg viewBox="0 0 700 720" xmlns="http://www.w3.org/2000/svg" role="presentation">
      <defs>
        <radialGradient id="halo"><stop offset="0" stopColor="#6c1919" stopOpacity=".4"/><stop offset="1" stopColor="#6c1919" stopOpacity="0"/></radialGradient>
        <pattern id="graticule" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M50 0H0V50" fill="none" stroke="#eee9de" strokeOpacity=".09" strokeWidth="1"/></pattern>
      </defs>
      <circle cx="370" cy="340" r="340" fill="url(#halo)"/>
      <circle cx="365" cy="355" r="268" fill="none" stroke="#b9ad9c" strokeOpacity=".22" strokeWidth="1"/>
      <circle cx="365" cy="355" r="215" fill="none" stroke="#b9ad9c" strokeOpacity=".11"/>
      <circle cx="365" cy="355" r="163" fill="none" stroke="#b9ad9c" strokeOpacity=".13"/>
      <circle cx="365" cy="355" r="110" fill="none" stroke="#b9ad9c" strokeOpacity=".10"/>
      <circle cx="365" cy="355" r="268" fill="url(#graticule)"/>
      <path d="M100 355H634 M365 87V623" stroke="#b9ad9c" strokeOpacity=".27"/>
      <ellipse cx="365" cy="355" rx="268" ry="95" fill="none" stroke="#b9ad9c" strokeOpacity=".21"/>
      <ellipse cx="365" cy="355" rx="95" ry="268" fill="none" stroke="#b9ad9c" strokeOpacity=".15"/>
      <g transform="translate(115 280) rotate(-13)">
        <path d="M22 78c28-34 48-43 64-48 11-5 19 4 24 11l22 72c6 19 0 31-13 43-18 13-21 31-29 35-5 4-14 0-16-11L22 78Z" fill="#e3ded5" fillOpacity=".2" stroke="#f0e9db" strokeOpacity=".55" strokeWidth="1.5"/>
        <path d="m180 165 122 4 26 17-120 2z" fill="#e3ded5" fillOpacity=".23" stroke="#f0e9db" strokeOpacity=".44"/>
        <path d="m210 53 42-17 27 13-1 19 35 5 21-17 15 13-15 19 14 23-26 26-44-6-7 28-33-15-13-33-30-17z" fill="#e3ded5" fillOpacity=".22" stroke="#f0e9db" strokeOpacity=".55" strokeWidth="1.5"/>
        <path d="m359 99 14-23 19 14-3 34 18 21-17 12-12-11-9 32-18 3 16-49-12-13z" fill="#e3ded5" fillOpacity=".18" stroke="#f0e9db" strokeOpacity=".45"/>
        <path d="m448 86 55-12 28 35-9 88-33 20-31-41z" fill="#e3ded5" fillOpacity=".18" stroke="#f0e9db" strokeOpacity=".46"/>
        <path d="m355 220 22 5m15 4 25 9m30-18 29 6m35-13 10 7m-220 18 13 4" stroke="#f0e9db" strokeOpacity=".48" strokeWidth="3" strokeLinecap="round"/>
      </g>
      <g fill="#d84a40" stroke="#d84a40"><circle cx="221" cy="384" r="5"/><circle cx="321" cy="341" r="6"/><circle cx="356" cy="415" r="4"/><circle cx="532" cy="365" r="5"/><circle cx="405" cy="393" r="3"/><circle cx="237" cy="394" r="2"/><circle cx="340" cy="351" r="3"/></g>
      <circle cx="321" cy="341" r="28" stroke="#d84a40" strokeOpacity=".7" fill="none"/><circle cx="321" cy="341" r="43" stroke="#d84a40" strokeOpacity=".28" fill="none"/>
      <g fill="#b9ad9c" fontFamily="monospace" fontSize="10" letterSpacing="1"><text x="110" y="105">94.9° E</text><text x="513" y="105">141.1° E</text><text x="108" y="610">11.0° S</text><text x="520" y="610">6.0° N</text><text x="374" y="355">IDN / OBSERVATORY</text></g>
    </svg>
    <span className="artwork-label">FIG. 01 / GEOSPATIAL MOTIF<br/>ILLUSTRATIVE · NOT OBSERVATIONAL DATA</span>
  </div>
}
