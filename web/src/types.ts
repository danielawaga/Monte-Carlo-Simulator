export type NumericRecord = Record<string, string | number | boolean | null>

export interface ProjectMetadata {
  name: string
  analysisType: 'cost' | 'duration'
  unit: string
  baseline: number | null
  description: string | null
}

export interface RunMetadata {
  simulations: number
  seed: number
  confidenceLevels: number[]
  correlationsEnabled: boolean
  generatedAt: string
}

export interface HistogramBin {
  start: number
  end: number
  count: number
}

export interface SCurvePoint {
  amount: number
  probability: number
}

export interface SimulationResponse {
  project: ProjectMetadata
  run: RunMetadata
  summary: NumericRecord
  percentiles: NumericRecord[]
  sensitivity: NumericRecord[]
  convergence: NumericRecord[]
  baselineComparison: NumericRecord[]
  correlationDiagnostics: NumericRecord[]
  histogram: HistogramBin[]
  sCurve: SCurvePoint[]
}

export interface SimulationRequest {
  file: File
  simulations: number
  seed: number
  confidenceLevels: number[]
}
