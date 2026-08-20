import { useMemo, useState, type PointerEvent } from 'react';
import type { SimulationResponse } from '../../types';
import { Card, CardTitle } from '../common';

const WIDTH = 540;
const LEFT = 48;
const TOP = 24;
const BOTTOM = 235;

function amount(value: number, unit: string) {
  return `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} ${unit}`;
}

export function LiveHistogramCard({ result }: { result: SimulationResponse }) {
  const [active, setActive] = useState<number | null>(null);
  const maxCount = Math.max(...result.histogram.map((bin) => bin.count), 1);
  const barWidth = WIDTH / Math.max(result.histogram.length, 1);
  return <Card className="histogram chart-card">
    <CardTitle>Distribution des coûts totaux</CardTitle>
    <div className="chart-plot chart-plot--histogram"><svg viewBox="0 0 640 290" role="img" aria-label="Histogramme réel des résultats simulés">
      <line x1={LEFT} y1={BOTTOM} x2={LEFT + WIDTH} y2={BOTTOM} className="axis" />
      {result.histogram.map((bin, index) => {
        const height = bin.count / maxCount * (BOTTOM - TOP);
        return <rect key={bin.start} className={`histogram-bar ${active === index ? 'is-active' : ''}`} x={LEFT + index * barWidth} y={BOTTOM - height} width={Math.max(barWidth - 2, 1)} height={height} tabIndex={0} aria-label={`${amount(bin.start, result.project.unit)} à ${amount(bin.end, result.project.unit)} : ${bin.count} simulations`} onPointerEnter={() => setActive(index)} onPointerLeave={() => setActive(null)} onFocus={() => setActive(index)} onBlur={() => setActive(null)} />;
      })}
      {active === null ? null : <g className="chart-tooltip" transform="translate(375 30)"><rect width="205" height="48" rx="5" /><text className="tooltip-title" x="10" y="18">{result.histogram[active].count.toLocaleString('fr-FR')} simulations</text><text className="tooltip-detail" x="10" y="36">{amount(result.histogram[active].start, result.project.unit)} – {amount(result.histogram[active].end, result.project.unit)}</text></g>}
    </svg></div>
  </Card>;
}

type CurveProps = { current: SimulationResponse; reference?: SimulationResponse | null };

export function LiveSCurveCard({ current, reference = null }: CurveProps) {
  const [active, setActive] = useState<number | null>(null);
  const maxAmount = useMemo(() => Math.max(
    current.sCurve.at(-1)?.amount ?? 1,
    reference?.sCurve.at(-1)?.amount ?? 1,
  ), [current, reference]);
  const path = (points: SimulationResponse['sCurve']) => points.map((point, index) => {
    const x = LEFT + point.amount / maxAmount * WIDTH;
    const y = BOTTOM - point.probability * (BOTTOM - TOP);
    return `${index ? 'L' : 'M'}${x} ${y}`;
  }).join(' ');
  const selectPoint = (event: PointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width * 640;
    const index = Math.round((x - LEFT) / WIDTH * (current.sCurve.length - 1));
    setActive(Math.min(Math.max(index, 0), current.sCurve.length - 1));
  };
  const point = active === null ? null : current.sCurve[active];
  return <Card className="curve chart-card">
    <CardTitle>{reference ? 'Comparaison des distributions cumulées' : 'Courbe de probabilité empirique (S-curve)'}</CardTitle>
    <div className="chart-legend">{reference ? <><span className="blue-solid">Référence</span><span className="green-solid">Scénario courant</span></> : <span className="orange-solid">Distribution cumulée réelle</span>}</div>
    <div className="chart-plot chart-plot--curve"><svg viewBox="0 0 640 290" role="img" aria-label="Courbe cumulative réelle" onPointerMove={selectPoint} onPointerLeave={() => setActive(null)}>
      <line x1={LEFT} y1={BOTTOM} x2={LEFT + WIDTH} y2={BOTTOM} className="axis" />
      {reference ? <path d={path(reference.sCurve)} className="curve-blue" /> : null}
      <path d={path(current.sCurve)} className={reference ? 'curve-green' : 'curve-orange'} />
      {point ? <><line x1={LEFT + point.amount / maxAmount * WIDTH} y1={TOP} x2={LEFT + point.amount / maxAmount * WIDTH} y2={BOTTOM} className="chart-crosshair" /><g className="chart-tooltip" transform="translate(365 30)"><rect width="215" height="48" rx="5" /><text className="tooltip-title" x="10" y="18">{amount(point.amount, current.project.unit)}</text><text className="tooltip-detail" x="10" y="36">Probabilité : {(point.probability * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %</text></g></> : null}
    </svg></div>
  </Card>;
}
