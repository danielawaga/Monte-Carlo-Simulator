import { useMemo, useState, type PointerEvent } from 'react';
import type { NumericRecord, SimulationResponse } from '../../types';
import { Card, CardTitle } from '../common';

const VIEW_WIDTH = 640;
const LEFT = 76;
const RIGHT = 610;
const TOP = 34;
const BOTTOM = 248;
const PLOT_WIDTH = RIGHT - LEFT;
const PLOT_HEIGHT = BOTTOM - TOP;

function amount(value: number, unit: string) {
  return `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} ${unit}`;
}

function compact(value: number, maximumFractionDigits = 1) {
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${(value / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits })} M`;
  if (absolute >= 1_000) return `${(value / 1_000).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} k`;
  return value.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

function numeric(record: NumericRecord | undefined, key: string) {
  const value = record?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function percentile(result: SimulationResponse, label: string) {
  return result.percentiles.find((row) => row.percentile === label);
}

function ticks(minimum: number, maximum: number, count = 5) {
  const range = maximum - minimum || 1;
  return Array.from({ length: count }, (_, index) => minimum + range * index / (count - 1));
}

function AnalysisAxis({ result }: { result: SimulationResponse }) {
  const label = result.project.analysisType === 'duration' ? 'Durée totale' : 'Coût total';
  return <text className="axis-title" x={(LEFT + RIGHT) / 2} y="290" textAnchor="middle">{label} ({result.project.unit})</text>;
}

function EmptyChart({ title, message }: { title: string; message: string }) {
  return <Card className="chart-card live-chart-card"><CardTitle info={false}>{title}</CardTitle><div className="chart-empty"><b>Données indisponibles</b><span>{message}</span></div></Card>;
}

type Marker = { label: string; value: number; className: string };

export function LiveHistogramCard({ result }: { result: SimulationResponse }) {
  const [active, setActive] = useState<number | null>(null);
  if (!result.histogram.length) return <EmptyChart title="Distribution" message="Le moteur n’a renvoyé aucune classe d’histogramme." />;

  const minimum = result.histogram[0].start;
  const maximum = result.histogram.at(-1)?.end ?? minimum + 1;
  const range = maximum - minimum || 1;
  const maxCount = Math.max(...result.histogram.map((bin) => bin.count), 1);
  const barWidth = PLOT_WIDTH / result.histogram.length;
  const mean = numeric(result.summary, 'mean');
  const p80 = numeric(percentile(result, 'P80'), 'amount');
  const p90 = numeric(percentile(result, 'P90'), 'amount');
  const markers: Marker[] = [
    mean === null ? null : { label: 'Moyenne', value: mean, className: 'mean' },
    p80 === null ? null : { label: 'P80', value: p80, className: 'p80' },
    p90 === null ? null : { label: 'P90', value: p90, className: 'p90' },
  ].filter((marker): marker is Marker => marker !== null && marker.value >= minimum && marker.value <= maximum);
  const title = result.project.analysisType === 'duration' ? 'Distribution de la durée totale' : 'Distribution du coût total';
  const activeBin = active === null ? null : result.histogram[active];

  return <Card className="histogram chart-card live-chart-card">
    <CardTitle info={false}>{title}</CardTitle>
    <div className="chart-legend">
      <span className="legend-fill">Fréquence</span>
      {markers.map((marker) => <span className={`legend-marker ${marker.className}`} key={marker.label}>{marker.label}</span>)}
    </div>
    <div className="chart-plot chart-plot--live"><svg viewBox="0 0 640 310" role="img" aria-label={`Histogramme réel de la ${title.toLowerCase()}`}>
      {ticks(0, maxCount).map((value) => {
        const y = BOTTOM - value / maxCount * PLOT_HEIGHT;
        return <g key={value}><line x1={LEFT} y1={y} x2={RIGHT} y2={y} className="chart-grid-line" /><text x={LEFT - 10} y={y + 3} textAnchor="end">{compact(value)}</text></g>;
      })}
      {ticks(minimum, maximum).map((value) => {
        const x = LEFT + (value - minimum) / range * PLOT_WIDTH;
        return <g key={value}><line x1={x} y1={TOP} x2={x} y2={BOTTOM} className="chart-grid-line vertical" /><text x={x} y={BOTTOM + 20} textAnchor="middle">{compact(value)}</text></g>;
      })}
      {result.histogram.map((bin, index) => {
        const height = bin.count / maxCount * PLOT_HEIGHT;
        return <rect key={`${bin.start}-${index}`} className={`histogram-bar ${active === index ? 'is-active' : ''}`} x={LEFT + index * barWidth + 1} y={BOTTOM - height} width={Math.max(barWidth - 2, 1)} height={height} tabIndex={0} aria-label={`${amount(bin.start, result.project.unit)} à ${amount(bin.end, result.project.unit)} : ${bin.count} simulations`} onPointerEnter={() => setActive(index)} onPointerLeave={() => setActive(null)} onFocus={() => setActive(index)} onBlur={() => setActive(null)} />;
      })}
      {markers.map((marker) => {
        const x = LEFT + (marker.value - minimum) / range * PLOT_WIDTH;
        return <g key={marker.label}><line x1={x} y1={TOP} x2={x} y2={BOTTOM} className={`live-marker ${marker.className}`} /><text className={`marker-label ${marker.className}`} x={x} y={TOP - 8} textAnchor="middle">{marker.label}</text></g>;
      })}
      <line x1={LEFT} y1={BOTTOM} x2={RIGHT} y2={BOTTOM} className="axis" />
      <line x1={LEFT} y1={TOP} x2={LEFT} y2={BOTTOM} className="axis" />
      <AnalysisAxis result={result} />
      {activeBin ? <g className="chart-tooltip" transform={`translate(${Math.min(390, LEFT + (active ?? 0) * barWidth + 14)} 48)`}><rect width="208" height="52" rx="5" /><text className="tooltip-title" x="10" y="20">{activeBin.count.toLocaleString('fr-FR')} simulations</text><text className="tooltip-detail" x="10" y="39">{compact(activeBin.start)} – {compact(activeBin.end)} {result.project.unit}</text></g> : null}
    </svg></div>
  </Card>;
}

type CurveProps = { current: SimulationResponse; reference?: SimulationResponse | null };

export function LiveSCurveCard({ current, reference = null }: CurveProps) {
  const [active, setActive] = useState<number | null>(null);
  const allPoints = reference ? [...current.sCurve, ...reference.sCurve] : current.sCurve;
  if (!current.sCurve.length) return <EmptyChart title="Courbe cumulative" message="Le moteur n’a renvoyé aucun point de probabilité cumulée." />;

  const minimum = Math.min(...allPoints.map((point) => point.amount));
  const maximum = Math.max(...allPoints.map((point) => point.amount));
  const range = maximum - minimum || 1;
  const toX = (value: number) => LEFT + (value - minimum) / range * PLOT_WIDTH;
  const toY = (probability: number) => BOTTOM - probability * PLOT_HEIGHT;
  const path = (points: SimulationResponse['sCurve']) => points.map((point, index) => `${index ? 'L' : 'M'}${toX(point.amount)} ${toY(point.probability)}`).join(' ');
  const markers = ['P80', 'P90'].map((label) => ({ label, value: numeric(percentile(current, label), 'amount'), probability: Number(label.slice(1)) / 100 })).filter((item): item is { label: string; value: number; probability: number } => item.value !== null);

  const selectPoint = (event: PointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const viewX = (event.clientX - bounds.left) / bounds.width * VIEW_WIDTH;
    const targetAmount = minimum + (viewX - LEFT) / PLOT_WIDTH * range;
    let nearest = 0;
    for (let index = 1; index < current.sCurve.length; index += 1) {
      if (Math.abs(current.sCurve[index].amount - targetAmount) < Math.abs(current.sCurve[nearest].amount - targetAmount)) nearest = index;
    }
    setActive(nearest);
  };
  const point = active === null ? null : current.sCurve[active];

  return <Card className="curve chart-card live-chart-card">
    <CardTitle info={false}>{reference ? 'Comparaison des distributions cumulées' : 'Courbe de probabilité empirique (S-curve)'}</CardTitle>
    <div className="chart-legend">{reference ? <><span className="blue-solid">Référence</span><span className="green-solid">Scénario courant</span></> : <><span className="orange-solid">Distribution cumulée</span><span className="legend-marker p80">P80</span><span className="legend-marker p90">P90</span></>}</div>
    <div className="chart-plot chart-plot--live"><svg viewBox="0 0 640 310" role="img" aria-label="Courbe cumulative réelle" onPointerMove={selectPoint} onPointerLeave={() => setActive(null)}>
      {[0, .25, .5, .75, 1].map((probability) => <g key={probability}><line x1={LEFT} y1={toY(probability)} x2={RIGHT} y2={toY(probability)} className="chart-grid-line" /><text x={LEFT - 10} y={toY(probability) + 3} textAnchor="end">{probability * 100} %</text></g>)}
      {ticks(minimum, maximum).map((value) => <g key={value}><line x1={toX(value)} y1={TOP} x2={toX(value)} y2={BOTTOM} className="chart-grid-line vertical" /><text x={toX(value)} y={BOTTOM + 20} textAnchor="middle">{compact(value)}</text></g>)}
      {reference ? <path d={path(reference.sCurve)} className="curve-blue" /> : null}
      <path d={path(current.sCurve)} className={reference ? 'curve-green' : 'curve-orange'} />
      {!reference ? markers.map((marker) => <g key={marker.label}><line x1={toX(marker.value)} y1={TOP} x2={toX(marker.value)} y2={BOTTOM} className={`live-marker ${marker.label.toLowerCase()}`} /><circle cx={toX(marker.value)} cy={toY(marker.probability)} r="4" className={`percentile-point ${marker.label.toLowerCase()}`} /><text className={`marker-label ${marker.label.toLowerCase()}`} x={toX(marker.value)} y={TOP - 8} textAnchor="middle">{marker.label}</text></g>) : null}
      <line x1={LEFT} y1={BOTTOM} x2={RIGHT} y2={BOTTOM} className="axis" /><line x1={LEFT} y1={TOP} x2={LEFT} y2={BOTTOM} className="axis" />
      <AnalysisAxis result={current} />
      {point ? <><line x1={toX(point.amount)} y1={TOP} x2={toX(point.amount)} y2={BOTTOM} className="chart-crosshair" /><circle className="curve-point distribution" cx={toX(point.amount)} cy={toY(point.probability)} r="4" /><g className="chart-tooltip" transform={`translate(${Math.min(390, Math.max(LEFT + 8, toX(point.amount) + 10))} 48)`}><rect width="210" height="52" rx="5" /><text className="tooltip-title" x="10" y="20">{amount(point.amount, current.project.unit)}</text><text className="tooltip-detail" x="10" y="39">Probabilité : {(point.probability * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %</text></g></> : null}
    </svg></div>
  </Card>;
}

export function TornadoChartCard({ result }: { result: SimulationResponse }) {
  const rows = useMemo(() => [...result.sensitivity]
    .filter((row) => typeof row.spearman_rho === 'number' && Number.isFinite(row.spearman_rho))
    .sort((left, right) => Math.abs(Number(right.spearman_rho)) - Math.abs(Number(left.spearman_rho)))
    .slice(0, 8), [result.sensitivity]);
  if (!rows.length) return <EmptyChart title="Sensibilité" message="Aucun coefficient de sensibilité n’est disponible." />;
  const maxAbsolute = Math.max(...rows.map((row) => Math.abs(Number(row.spearman_rho))), .01);
  const center = 405;
  const width = 170;
  const rowHeight = 30;
  const chartBottom = 52 + rows.length * rowHeight;
  return <Card className="chart-card live-chart-card tornado-card"><CardTitle info={false}>Diagramme Tornado — sensibilité de Spearman</CardTitle><div className="chart-plot tornado-plot"><svg viewBox={`0 0 640 ${chartBottom + 32}`} role="img" aria-label="Diagramme Tornado des postes les plus sensibles">
    <line x1={center} y1="32" x2={center} y2={chartBottom} className="tornado-zero" />
    <text x={center - width} y="20" textAnchor="middle">−1</text><text x={center} y="20" textAnchor="middle">0</text><text x={center + width} y="20" textAnchor="middle">+1</text>
    {rows.map((row, index) => {
      const coefficient = Number(row.spearman_rho);
      const bar = Math.abs(coefficient) / maxAbsolute * width;
      const y = 42 + index * rowHeight;
      const name = String(row.item_name);
      const shortName = name.length > 30 ? `${name.slice(0, 29)}…` : name;
      return <g key={`${name}-${index}`}><text x="12" y={y + 14} className="tornado-label">{shortName}</text><rect x={coefficient >= 0 ? center : center - bar} y={y} width={bar} height="18" rx="3" className={coefficient >= 0 ? 'tornado-positive' : 'tornado-negative'} /><text x={coefficient >= 0 ? center + bar + 7 : center - bar - 7} y={y + 13} textAnchor={coefficient >= 0 ? 'start' : 'end'} className="tornado-value">{coefficient.toLocaleString('fr-FR', { maximumFractionDigits: 3, signDisplay: 'always' })}</text></g>;
    })}
  </svg></div></Card>;
}

export function ConvergenceChartCard({ result }: { result: SimulationResponse }) {
  const [active, setActive] = useState<number | null>(null);
  const rows = result.convergence.filter((row) => numeric(row, 'draw_count') !== null && numeric(row, 'estimate') !== null);
  if (!rows.length) return <EmptyChart title="Convergence" message="Aucun diagnostic de convergence n’est disponible." />;
  const draws = rows.map((row) => numeric(row, 'draw_count') as number);
  const estimates = rows.map((row) => numeric(row, 'estimate') as number);
  const minimumDraw = Math.min(...draws);
  const maximumDraw = Math.max(...draws);
  const estimateMinimum = Math.min(...estimates);
  const estimateMaximum = Math.max(...estimates);
  const estimatePadding = Math.max((estimateMaximum - estimateMinimum) * .15, Math.abs(estimateMaximum) * .005, 1);
  const yMinimum = estimateMinimum - estimatePadding;
  const yMaximum = estimateMaximum + estimatePadding;
  const toX = (value: number) => LEFT + (value - minimumDraw) / (maximumDraw - minimumDraw || 1) * PLOT_WIDTH;
  const toY = (value: number) => BOTTOM - (value - yMinimum) / (yMaximum - yMinimum || 1) * PLOT_HEIGHT;
  const path = estimates.map((estimate, index) => `${index ? 'L' : 'M'}${toX(draws[index])} ${toY(estimate)}`).join(' ');
  const selected = active === null ? null : rows[active];
  const selectPoint = (event: PointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const viewX = (event.clientX - bounds.left) / bounds.width * VIEW_WIDTH;
    const index = Math.round((viewX - LEFT) / PLOT_WIDTH * (rows.length - 1));
    setActive(Math.min(Math.max(index, 0), rows.length - 1));
  };
  return <Card className="chart-card live-chart-card convergence-card"><CardTitle info={false}>Convergence du percentile cible</CardTitle><div className="chart-legend"><span className="orange-solid">Estimation cumulative</span><span className="stable-dot">Bloc stable</span></div><div className="chart-plot chart-plot--live"><svg viewBox="0 0 640 310" role="img" aria-label="Courbe de convergence du percentile cible" onPointerMove={selectPoint} onPointerLeave={() => setActive(null)}>
    {ticks(yMinimum, yMaximum).map((value) => <g key={value}><line x1={LEFT} y1={toY(value)} x2={RIGHT} y2={toY(value)} className="chart-grid-line" /><text x={LEFT - 10} y={toY(value) + 3} textAnchor="end">{compact(value, 2)}</text></g>)}
    {ticks(minimumDraw, maximumDraw, 4).map((value) => <g key={value}><line x1={toX(value)} y1={TOP} x2={toX(value)} y2={BOTTOM} className="chart-grid-line vertical" /><text x={toX(value)} y={BOTTOM + 20} textAnchor="middle">{compact(value)}</text></g>)}
    <path d={path} className="convergence-line" />
    {rows.map((row, index) => <circle key={draws[index]} cx={toX(draws[index])} cy={toY(estimates[index])} r="4" className={row.within_tolerance === true ? 'convergence-point stable' : 'convergence-point'} />)}
    <line x1={LEFT} y1={BOTTOM} x2={RIGHT} y2={BOTTOM} className="axis" /><line x1={LEFT} y1={TOP} x2={LEFT} y2={BOTTOM} className="axis" />
    <text className="axis-title" x={(LEFT + RIGHT) / 2} y="290" textAnchor="middle">Nombre de tirages</text>
    {selected ? <g className="chart-tooltip" transform="translate(386 48)"><rect width="214" height="68" rx="5" /><text className="tooltip-title" x="10" y="20">{Number(selected.draw_count).toLocaleString('fr-FR')} tirages</text><text className="tooltip-detail" x="10" y="40">Estimation : {compact(Number(selected.estimate))} {result.project.unit}</text><text className="tooltip-detail" x="10" y="58">{selected.within_tolerance === true ? 'Dans la tolérance' : 'Variation encore significative'}</text></g> : null}
  </svg></div></Card>;
}
