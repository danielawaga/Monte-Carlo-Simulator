import { DragEvent, useMemo, useRef, useState } from 'react'
import { runSimulation } from './api'
import type { HistogramBin, NumericRecord, SCurvePoint, SimulationResponse } from './types'

const LEVELS = [0.5, 0.8, 0.9, 0.95]

function numberFrom(record: NumericRecord | undefined, key: string): number | null {
  const value = record?.[key]
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function formatNumber(value: number | null | undefined, unit?: string, compact = false): string {
  if (value == null || !Number.isFinite(value)) return '—'
  const formatter = new Intl.NumberFormat('fr-FR', {
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 2 : Math.abs(value) >= 1000 ? 0 : 2,
  })
  return `${formatter.format(value)}${unit ? ` ${unit}` : ''}`
}

function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('fr-FR', {
    style: 'percent',
    maximumFractionDigits: digits,
  }).format(value)
}

function Metric({ label, value, note, accent }: { label: string; value: string; note: string; accent?: boolean }) {
  return (
    <article className={`metric ${accent ? 'metric--accent' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

function Histogram({ bins, unit }: { bins: HistogramBin[]; unit: string }) {
  const width = 720
  const height = 230
  const pad = 26
  const max = Math.max(...bins.map((bin) => bin.count), 1)
  const innerWidth = width - pad * 2
  const innerHeight = height - pad * 2
  const barWidth = innerWidth / Math.max(bins.length, 1)

  return (
    <div className="chart-shell">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Histogramme de la distribution simulée">
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} className="axis" />
        {bins.map((bin, index) => {
          const h = (bin.count / max) * innerHeight
          const x = pad + index * barWidth
          return (
            <rect
              key={`${bin.start}-${index}`}
              x={x + 1}
              y={height - pad - h}
              width={Math.max(barWidth - 2, 1)}
              height={h}
              rx="2"
              className="histogram-bar"
            />
          )
        })}
      </svg>
      <div className="chart-scale">
        <span>{formatNumber(bins[0]?.start, unit, true)}</span>
        <span>{formatNumber(bins[bins.length - 1]?.end, unit, true)}</span>
      </div>
    </div>
  )
}

function SCurve({ points, unit }: { points: SCurvePoint[]; unit: string }) {
  const width = 720
  const height = 230
  const pad = 28
  if (!points.length) return null
  const xMin = points[0].amount
  const xMax = points[points.length - 1].amount
  const xSpan = xMax - xMin || 1
  const path = points
    .map((point, index) => {
      const x = pad + ((point.amount - xMin) / xSpan) * (width - pad * 2)
      const y = height - pad - point.probability * (height - pad * 2)
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`
    })
    .join(' ')

  return (
    <div className="chart-shell">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Courbe cumulative de probabilité">
        {[0.25, 0.5, 0.75].map((tick) => {
          const y = height - pad - tick * (height - pad * 2)
          return <line key={tick} x1={pad} y1={y} x2={width - pad} y2={y} className="gridline" />
        })}
        <path d={path} className="s-curve" />
      </svg>
      <div className="chart-scale">
        <span>{formatNumber(xMin, unit, true)}</span>
        <span>probabilité cumulée</span>
        <span>{formatNumber(xMax, unit, true)}</span>
      </div>
    </div>
  )
}

function Sensitivity({ rows }: { rows: NumericRecord[] }) {
  const defined = rows
    .filter((row) => row.is_defined === true && typeof row.absolute_rho === 'number')
    .slice(0, 7)
  const max = Math.max(...defined.map((row) => Number(row.absolute_rho)), 0.01)

  if (!defined.length) return <p className="empty-copy">Aucune sensibilité exploitable pour ce run.</p>

  return (
    <div className="sensitivity-list">
      {defined.map((row) => {
        const rho = Number(row.spearman_rho)
        const absolute = Number(row.absolute_rho)
        return (
          <div className="sensitivity-row" key={String(row.item_name)}>
            <div>
              <strong>{String(row.item_name)}</strong>
              <span>ρ = {rho.toFixed(3)}</span>
            </div>
            <div className="sensitivity-track">
              <i style={{ width: `${(absolute / max) * 100}%` }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function PercentileRail({ rows, unit }: { rows: NumericRecord[]; unit: string }) {
  return (
    <div className="percentile-rail">
      {rows.map((row) => {
        const label = String(row.percentile ?? '')
        const amount = numberFrom(row, 'amount')
        const reserve = numberFrom(row, 'recommended_reserve')
        return (
          <div className="percentile-step" key={label}>
            <span>{label}</span>
            <strong>{formatNumber(amount, unit)}</strong>
            <small>{reserve == null ? 'sans baseline' : `réserve ${formatNumber(reserve, unit)}`}</small>
          </div>
        )
      })}
    </div>
  )
}

function ScenarioDelta({ reference, current }: { reference: SimulationResponse; current: SimulationResponse }) {
  const unit = current.project.unit
  const compatible =
    reference.project.analysisType === current.project.analysisType &&
    reference.project.unit === current.project.unit
  const keys = ['P50', 'P80', 'P90', 'P95']

  if (!compatible) {
    return (
      <div className="scenario-placeholder">
        <strong>Comparaison impossible sur une même échelle.</strong>
        <span>Le scénario de référence et le run actuel doivent utiliser le même type d’analyse et la même unité.</span>
      </div>
    )
  }

  return (
    <div className="scenario-table">
      <div className="scenario-head">
        <span>Niveau</span><span>Référence</span><span>Actuel</span><span>Écart</span>
      </div>
      {keys.map((key) => {
        const left = numberFrom(reference.summary, key)
        const right = numberFrom(current.summary, key)
        if (left == null && right == null) return null
        const delta = left != null && right != null ? right - left : null
        return (
          <div className="scenario-line" key={key}>
            <strong>{key}</strong>
            <span>{formatNumber(left, unit, true)}</span>
            <span>{formatNumber(right, unit, true)}</span>
            <span className={delta != null && delta > 0 ? 'delta-up' : 'delta-down'}>
              {delta == null ? '—' : `${delta > 0 ? '+' : ''}${formatNumber(delta, unit, true)}`}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [simulations, setSimulations] = useState(10_000)
  const [seed, setSeed] = useState(42)
  const [levels, setLevels] = useState<number[]>([0.5, 0.8, 0.9, 0.95])
  const [result, setResult] = useState<SimulationResponse | null>(null)
  const [reference, setReference] = useState<SimulationResponse | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  const unit = result?.project.unit ?? ''
  const baselineProbability = useMemo(() => {
    const row = result?.baselineComparison[0]
    return row ? numberFrom(row, 'exceedance_probability') : null
  }, [result])

  function chooseFile(next: File | undefined) {
    if (!next) return
    if (!next.name.toLowerCase().endsWith('.xlsx')) {
      setError('Le registre doit être un fichier .xlsx conforme au schéma 1.0.')
      return
    }
    setFile(next)
    setError(null)
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    chooseFile(event.dataTransfer.files[0])
  }

  function toggleLevel(level: number) {
    setLevels((current) => {
      if (current.includes(level)) {
        if (current.length === 1) return current
        return current.filter((item) => item !== level)
      }
      return [...current, level].sort()
    })
  }

  async function execute() {
    if (!file) {
      setError('Ajoutez d’abord un registre de risques Excel.')
      return
    }
    setRunning(true)
    setError(null)
    try {
      const next = await runSimulation({ file, simulations, seed, confidenceLevels: levels })
      setResult(next)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'La simulation a échoué.')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Monte Carlo Risk Studio">
          <span className="brand-mark">MC</span>
          <span><strong>Risk Studio</strong><small>Monte Carlo Simulator</small></span>
        </a>
        <div className="engine-state"><i /> moteur Python <span>·</span> interface S5</div>
      </header>

      <aside className="control-panel">
        <div className="control-kicker">Nouveau run</div>
        <h2>Configurer la simulation</h2>
        <p className="muted">Le calcul reste exécuté par le moteur Python validé. L’interface ne réimplémente aucune règle probabiliste.</p>

        <label className="field-label">Registre de risques</label>
        <div
          className={`dropzone ${dragging ? 'dropzone--active' : ''}`}
          onDragEnter={(event) => { event.preventDefault(); setDragging(true) }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input ref={inputRef} hidden type="file" accept=".xlsx" onChange={(event) => chooseFile(event.target.files?.[0])} />
          <span className="drop-icon">↗</span>
          <strong>{file ? file.name : 'Déposer le registre Excel'}</strong>
          <small>{file ? `${(file.size / 1024).toFixed(0)} Ko · prêt à simuler` : '.xlsx · schéma 1.0 · max. 12 Mo'}</small>
        </div>
        <a className="template-link" href="/api/template">Télécharger le modèle Excel →</a>

        <div className="field-row">
          <label>
            <span>Simulations</span>
            <input type="number" min={1000} max={1_000_000} step={1000} value={simulations} onChange={(e) => setSimulations(Number(e.target.value))} />
          </label>
          <label>
            <span>Graine</span>
            <input type="number" min={0} value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
          </label>
        </div>

        <label className="field-label">Niveaux de décision</label>
        <div className="level-switches">
          {LEVELS.map((level) => (
            <button type="button" key={level} className={levels.includes(level) ? 'active' : ''} onClick={() => toggleLevel(level)}>
              P{level * 100}
            </button>
          ))}
        </div>

        {error && <div className="error-box">{error}</div>}

        <button className="run-button" type="button" onClick={execute} disabled={running}>
          <span>{running ? 'Simulation en cours…' : 'Lancer le run'}</span>
          <b>{running ? '···' : '→'}</b>
        </button>

        <div className="control-footnote">
          <span>Reproductible</span><span>Corrélations</span><span>Spearman</span>
        </div>
      </aside>

      <main className="workspace" id="top">
        <section className="hero">
          <div>
            <span className="eyebrow">S5 · interface décisionnelle</span>
            <h1>Décider avec une <em>distribution</em>, pas une marge arbitraire.</h1>
          </div>
          <p>Une lecture plus directe des percentiles, de l’exposition budgétaire et des facteurs qui déplacent réellement le risque.</p>
        </section>

        {!result ? (
          <section className="empty-stage">
            <div className="empty-grid" />
            <div className="empty-copy-block">
              <span>01</span>
              <h3>Chargez un registre puis lancez une simulation.</h3>
              <p>Le tableau de bord apparaîtra ici : P50/P80/P90, distribution, S-curve, sensibilité et comparaison de scénarios.</p>
            </div>
          </section>
        ) : (
          <>
            <section className="project-strip">
              <div>
                <span>Projet</span>
                <strong>{result.project.name}</strong>
              </div>
              <div><span>Analyse</span><strong>{result.project.analysisType === 'cost' ? 'Coût' : 'Durée'}</strong></div>
              <div><span>Tirages</span><strong>{result.run.simulations.toLocaleString('fr-FR')}</strong></div>
              <div><span>Corrélations</span><strong>{result.run.correlationsEnabled ? 'Actives' : 'Indépendant'}</strong></div>
              <button type="button" onClick={() => setReference(result)}>Geler comme référence</button>
            </section>

            <section className="metrics-grid">
              <Metric label="Moyenne simulée" value={formatNumber(numberFrom(result.summary, 'mean'), unit)} note="centre de la distribution" />
              <Metric label="P80" value={formatNumber(numberFrom(result.summary, 'P80'), unit)} note="20 % de probabilité de dépassement" accent />
              <Metric label="P90" value={formatNumber(numberFrom(result.summary, 'P90'), unit)} note="niveau prudent" />
              <Metric label="Dépassement baseline" value={formatPercent(baselineProbability)} note={result.project.baseline == null ? 'aucune baseline renseignée' : `baseline ${formatNumber(result.project.baseline, unit)}`} />
            </section>

            <section className="decision-layout">
              <article className="panel panel--wide">
                <div className="panel-heading">
                  <div><span>Distribution</span><h2>Où se situe l’exposition ?</h2></div>
                  <small>{result.project.analysisType === 'cost' ? 'coût total simulé' : 'durée totale simulée'}</small>
                </div>
                <Histogram bins={result.histogram} unit={unit} />
              </article>

              <article className="panel panel--rail">
                <div className="panel-heading"><div><span>Niveaux</span><h2>Lecture décisionnelle</h2></div></div>
                <PercentileRail rows={result.percentiles} unit={unit} />
              </article>
            </section>

            <section className="decision-layout decision-layout--reverse">
              <article className="panel panel--rail panel--ink">
                <div className="panel-heading"><div><span>Sensibilité</span><h2>Ce qui déplace le résultat</h2></div></div>
                <Sensitivity rows={result.sensitivity} />
              </article>

              <article className="panel panel--wide">
                <div className="panel-heading">
                  <div><span>S-curve</span><h2>Probabilité de rester sous un seuil</h2></div>
                  <small>lecture budget ↔ confiance</small>
                </div>
                <SCurve points={result.sCurve} unit={unit} />
              </article>
            </section>

            <section className="scenario-section">
              <div className="scenario-intro">
                <span>Comparaison de scénarios</span>
                <h2>Mesurer l’effet d’une mitigation sans perdre le scénario de départ.</h2>
                <p>Gelez un run comme référence, modifiez le registre Excel, puis relancez. Les écarts de percentiles sont comparés sur la même échelle.</p>
              </div>
              <div className="scenario-content">
                {reference ? <ScenarioDelta reference={reference} current={result} /> : (
                  <div className="scenario-placeholder">
                    <strong>Aucune référence gelée.</strong>
                    <span>Utilisez « Geler comme référence » sur un run avant de tester un scénario mitigé.</span>
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
