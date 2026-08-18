import { useState, type PointerEvent } from 'react';
import { Card, CardTitle } from '../common';

const GRID_LINES = [30, 75, 120, 165, 210];
const HISTOGRAM_HEIGHTS = [4, 10, 25, 55, 105, 155, 190, 210, 200, 184, 170, 140, 136, 115, 100, 84, 72, 58, 44, 38, 32, 25, 20, 16, 14, 12, 10, 9, 7, 6, 5, 4];
const HISTOGRAM_TOTAL = HISTOGRAM_HEIGHTS.reduce((total, value) => total + value, 0);
const HISTOGRAM_SIMULATIONS = 50_000;
const RESULT_CURVE_COSTS = Array.from({ length: 21 }, (_, index) => index / 2);
const RESULT_PROBABILITIES = [0, 0.5, 2, 8, 30, 52, 65, 73, 79, 83, 86, 88, 89.5, 91, 93, 95, 97, 98.5, 99.3, 99.8, 100];
const COMPARISON_COSTS = RESULT_CURVE_COSTS;
const COMPARISON_REFERENCE_PROBABILITIES = RESULT_PROBABILITIES;
const COMPARISON_MITIGATION_PROBABILITIES = [0, 1, 4, 12, 32, 55, 68, 79, 84, 87, 89.5, 92, 94, 95.5, 97, 98, 98.8, 99.3, 99.6, 99.9, 100];

const toX = (cost: number, maxCost: number) => 50 + cost / maxCost * 540;
const toY = (probability: number) => 235 - probability * 2.03;
const formatCost = (cost: number) => `${cost.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} M€`;
const formatProbability = (probability: number) => `${probability.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`;

const Grid = () => (
  <>
    {GRID_LINES.map((y) => <line key={y} x1="48" y1={y} x2="590" y2={y} className="grid" />)}
  </>
);

const ChartAxis = ({ maxCost = 10 }: { maxCost?: number }) => (
  <>
    <line x1="48" y1="235" x2="590" y2="235" className="axis" />
    {Array.from({ length: 11 }, (_, index) => index * maxCost / 10).map((value, index) => (
      <text x={48 + index * 54} y="257" key={value}>{value === 0 ? '0' : `${value.toLocaleString('fr-FR')}M`}</text>
    ))}
    <text x="275" y="282">Coût total (€)</text>
  </>
);

function HistogramTooltip({ index }: { index: number }) {
  const height = HISTOGRAM_HEIGHTS[index];
  const x = 70 + index * 16;
  const tooltipX = Math.min(Math.max(x - 60, 50), 435);
  const tooltipY = Math.max(28, 225 - height);
  const start = index * 0.3125;
  const end = (index + 1) * 0.3125;
  const simulations = Math.round(height / HISTOGRAM_TOTAL * HISTOGRAM_SIMULATIONS);

  return (
    <g className="chart-tooltip" transform={`translate(${tooltipX} ${tooltipY})`}>
      <rect width="155" height="48" rx="5" />
      <text className="tooltip-title" x="10" y="18">{formatCost(start)} – {formatCost(end)}</text>
      <text className="tooltip-detail" x="10" y="36">{simulations.toLocaleString('fr-FR')} simulations</text>
    </g>
  );
}

export function HistogramCard() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const activeDescription = activeIndex === null
    ? ''
    : `Intervalle ${formatCost(activeIndex * 0.3125)} à ${formatCost((activeIndex + 1) * 0.3125)}, ${Math.round(HISTOGRAM_HEIGHTS[activeIndex] / HISTOGRAM_TOTAL * HISTOGRAM_SIMULATIONS).toLocaleString('fr-FR')} simulations.`;

  return (
    <Card className="histogram chart-card">
      <CardTitle>Distribution des coûts totaux</CardTitle>
      <div className="chart-legend">
        <span className="orange-line">Moyenne</span><span className="blue-line">P80</span><span className="gray-line">P90</span>
      </div>
      <div className="chart-plot chart-plot--histogram">
        <svg viewBox="0 0 640 290" role="img" aria-label="Histogramme interactif de la distribution des coûts">
          <Grid />
          {HISTOGRAM_HEIGHTS.map((height, index) => {
            const start = index * 0.3125;
            const end = (index + 1) * 0.3125;
            const simulations = Math.round(height / HISTOGRAM_TOTAL * HISTOGRAM_SIMULATIONS);
            return (
              <rect
                key={index}
                className={`histogram-bar ${activeIndex === index ? 'is-active' : ''}`}
                x={70 + index * 16}
                y={235 - height}
                width="12"
                height={height}
                rx="1"
                tabIndex={0}
                aria-label={`${formatCost(start)} à ${formatCost(end)} : ${simulations.toLocaleString('fr-FR')} simulations`}
                onPointerEnter={() => setActiveIndex(index)}
                onFocus={() => setActiveIndex(index)}
                onBlur={() => setActiveIndex(null)}
              />
            );
          })}
          <line x1="210" y1="26" x2="210" y2="235" className="marker orange" />
          <line x1="330" y1="26" x2="330" y2="235" className="marker blue" />
          <line x1="465" y1="26" x2="465" y2="235" className="marker gray" />
          <ChartAxis />
          {activeIndex === null ? null : <HistogramTooltip index={activeIndex} />}
        </svg>
        <p className="sr-only" aria-live="polite">{activeDescription}</p>
      </div>
    </Card>
  );
}

function CurveTooltip({
  cost,
  referenceProbability,
  mitigationProbability,
}: {
  cost: number;
  referenceProbability: number;
  mitigationProbability?: number;
}) {
  const comparison = mitigationProbability !== undefined;
  const maxCost = 10;
  const x = toX(cost, maxCost);
  const tooltipX = Math.min(Math.max(x - 75, 52), 418);

  return (
    <g className="chart-tooltip" transform={`translate(${tooltipX} 38)`}>
      <rect width="170" height={comparison ? 62 : 46} rx="5" />
      <text className="tooltip-title" x="10" y="18">Coût : {formatCost(cost)}</text>
      <text className="tooltip-detail" x="10" y="36">
        {comparison ? `Référence : ${formatProbability(referenceProbability)}` : `Probabilité : ${formatProbability(referenceProbability)}`}
      </text>
      {comparison ? <text className="tooltip-detail" x="10" y="53">Mitigation : {formatProbability(mitigationProbability)}</text> : null}
    </g>
  );
}

export function SCurveCard({ comparison = false }: { comparison?: boolean }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const costs = comparison ? COMPARISON_COSTS : RESULT_CURVE_COSTS;
  const referenceProbabilities = comparison ? COMPARISON_REFERENCE_PROBABILITIES : RESULT_PROBABILITIES;
  const mitigationProbabilities = comparison ? COMPARISON_MITIGATION_PROBABILITIES : null;
  const maxCost = 10;
  const referencePath = costs.map((cost, index) => `${index === 0 ? 'M' : 'L'}${toX(cost, maxCost)} ${toY(referenceProbabilities[index])}`).join(' ');
  const mitigationPath = mitigationProbabilities === null ? '' : costs.map((cost, index) => `${index === 0 ? 'M' : 'L'}${toX(cost, maxCost)} ${toY(mitigationProbabilities[index])}`).join(' ');

  const selectNearestPoint = (event: PointerEvent<SVGSVGElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const viewX = (event.clientX - bounds.left) / bounds.width * 640;
    const index = Math.round((viewX - 50) / 27);
    setActiveIndex(Math.min(Math.max(index, 0), costs.length - 1));
  };

  const activeDescription = activeIndex === null
    ? ''
    : comparison
      ? `Coût ${formatCost(costs[activeIndex])}, référence ${formatProbability(referenceProbabilities[activeIndex])}, mitigation ${formatProbability(COMPARISON_MITIGATION_PROBABILITIES[activeIndex])}.`
      : `Coût ${formatCost(costs[activeIndex])}, probabilité cumulée ${formatProbability(referenceProbabilities[activeIndex])}.`;

  return (
    <Card className="curve chart-card">
      <CardTitle>{comparison ? 'Comparaison des distributions cumulées' : 'Courbe de probabilité empirique (S-curve)'}</CardTitle>
      <div className="chart-legend">
        {comparison ? (
          <><span className="blue-solid">Référence</span><span className="green-solid">Mitigation</span></>
        ) : (
          <><span className="orange-solid">Distribution cumulée</span><span className="blue-line">P80</span><span className="gray-line">P90</span></>
        )}
      </div>
      <div className="chart-plot chart-plot--curve">
        <svg
          viewBox="0 0 640 290"
          role="img"
          aria-label={comparison ? 'Comparaison interactive des distributions cumulées' : 'Courbe interactive de probabilité empirique'}
          onPointerMove={selectNearestPoint}
          onPointerLeave={() => setActiveIndex(null)}
        >
          <Grid />
          <path d={referencePath} className={comparison ? 'curve-blue' : 'curve-orange'} />
          {comparison ? <path d={mitigationPath} className="curve-green" /> : null}
          {!comparison ? <>
            <line x1={toX(4.12, maxCost)} y1="26" x2={toX(4.12, maxCost)} y2="235" className="marker blue" />
            <line x1={toX(6.24, maxCost)} y1="26" x2={toX(6.24, maxCost)} y2="235" className="marker gray" />
          </> : null}
          <ChartAxis maxCost={maxCost} />
          {costs.map((cost, index) => (
            <circle
              key={cost}
              className="curve-hit-target"
              cx={toX(cost, maxCost)}
              cy={toY(referenceProbabilities[index])}
              r="8"
              tabIndex={0}
              aria-label={comparison
                ? `${formatCost(cost)} : référence ${formatProbability(referenceProbabilities[index])}, mitigation ${formatProbability(COMPARISON_MITIGATION_PROBABILITIES[index])}`
                : `${formatCost(cost)} : ${formatProbability(referenceProbabilities[index])}`}
              onFocus={() => setActiveIndex(index)}
              onBlur={() => setActiveIndex(null)}
            />
          ))}
          {activeIndex === null ? null : <>
            <line x1={toX(costs[activeIndex], maxCost)} y1="26" x2={toX(costs[activeIndex], maxCost)} y2="235" className="chart-crosshair" />
            <circle className={comparison ? 'curve-point reference' : 'curve-point distribution'} cx={toX(costs[activeIndex], maxCost)} cy={toY(referenceProbabilities[activeIndex])} r="4" />
            {comparison ? <circle className="curve-point mitigation" cx={toX(costs[activeIndex], maxCost)} cy={toY(COMPARISON_MITIGATION_PROBABILITIES[activeIndex])} r="4" /> : null}
            <CurveTooltip
              cost={costs[activeIndex]}
              referenceProbability={referenceProbabilities[activeIndex]}
              mitigationProbability={comparison ? COMPARISON_MITIGATION_PROBABILITIES[activeIndex] : undefined}
            />
          </>}
        </svg>
        <p className="sr-only" aria-live="polite">{activeDescription}</p>
      </div>
    </Card>
  );
}
