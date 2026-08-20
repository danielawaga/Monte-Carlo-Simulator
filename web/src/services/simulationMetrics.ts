import type { NumericRecord, SimulationResponse } from '../types';

export function percentile(result: SimulationResponse, label: string): NumericRecord | undefined {
  return result.percentiles.find((row) => row.percentile === label);
}

export function numeric(record: NumericRecord | undefined, key: string): number | null {
  const value = record?.[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

export function formatAmount(value: number | null, unit: string): string {
  return value === null ? 'Non disponible' : `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} ${unit}`;
}

export function formatVariation(reference: number | null, current: number | null): string {
  if (reference === null || current === null || reference === 0) return 'Non disponible';
  return `${((current - reference) / reference * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1, signDisplay: 'always' })} %`;
}

export function comparisonRows(reference: SimulationResponse, current: SimulationResponse) {
  const fields = [
    ['Moyenne', numeric(reference.summary, 'mean'), numeric(current.summary, 'mean')],
    ['P80', numeric(percentile(reference, 'P80'), 'amount'), numeric(percentile(current, 'P80'), 'amount')],
    ['P90', numeric(percentile(reference, 'P90'), 'amount'), numeric(percentile(current, 'P90'), 'amount')],
    ['Réserve recommandée (P80)', numeric(percentile(reference, 'P80'), 'recommended_reserve'), numeric(percentile(current, 'P80'), 'recommended_reserve')],
  ] as const;
  return fields.map(([label, referenceValue, currentValue]) => ({
    label,
    reference: referenceValue,
    current: currentValue,
    difference: referenceValue === null || currentValue === null ? null : currentValue - referenceValue,
    variation: formatVariation(referenceValue, currentValue),
  }));
}
