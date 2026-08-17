import type { SimulationRequest, SimulationResponse } from './types'

function errorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

export async function runSimulation(request: SimulationRequest): Promise<SimulationResponse> {
  const body = new FormData()
  body.append('file', request.file)
  body.append('simulations', String(request.simulations))
  body.append('seed', String(request.seed))
  body.append('confidence_levels', request.confidenceLevels.join(','))

  const response = await fetch('/api/simulate', { method: 'POST', body })
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(errorMessage(payload, `La simulation a échoué (${response.status}).`))
  }
  return payload as SimulationResponse
}
