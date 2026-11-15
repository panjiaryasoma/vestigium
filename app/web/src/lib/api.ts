import type { Sensor } from './types'

const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export async function getJson<T>(path: string, params?: Record<string, string | number | undefined | null>, signal?: AbortSignal): Promise<T> {
  const query = new URLSearchParams()
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value))
  })
  const response = await fetch(`${BASE}${path}${query.size ? `?${query}` : ''}`, { signal })
  if (!response.ok) throw new Error(`API request failed: ${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}

export function sensorLabel(sensor: Sensor | string): string {
  return ({ ALL: 'All sensors', MODIS: 'MODIS', VIIRS_SNPP: 'VIIRS S-NPP', VIIRS_NOAA20: 'VIIRS NOAA-20' } as Record<string, string>)[sensor] || sensor
}

export const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
export const FULL_MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
export const numberFormat = (value: number | null | undefined) => value == null ? '—' : Intl.NumberFormat('en-US').format(Math.round(value))
