import { useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import { Header } from './components/Brand'
import { getJson } from './lib/api'
import type { Meta } from './lib/types'
import Home from './pages/Home'
import Explore from './pages/Explore'
import Archive from './pages/Archive'
import Analysis from './pages/Analysis'
import Impact from './pages/Impact'
import Methodology from './pages/Methodology'
import './styles.css'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }) }, [pathname])
  return null
}

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  useEffect(() => { getJson<Meta>('/api/v1/meta').then(setMeta).catch(() => setMeta(null)) }, [])
  return <BrowserRouter><ScrollToTop/><Header mode={meta?.mode}/><Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/explore" element={<Explore meta={meta}/>}/>
    <Route path="/archive" element={<Archive meta={meta}/>}/>
    <Route path="/analysis" element={<Analysis meta={meta}/>}/>
    <Route path="/impact" element={<Impact/>}/>
    <Route path="/methodology" element={<Methodology/>}/>
    <Route path="*" element={<Home/>}/>
  </Routes></BrowserRouter>
}
