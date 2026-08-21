import type { RiskRegisterDraft, SimulationResponse } from '../types';

export const riskRegisterFixture: RiskRegisterDraft = {
  schemaVersion: '1.0',
  metadata: {
    projectName: 'Projet importé',
    analysisType: 'cost',
    defaultUnit: 'MAD',
    baselineEstimate: 2500000,
    description: 'Registre utilisé par les tests React.',
  },
  items: [{
    id: 'risk-1',
    name: 'Études',
    distribution: 'triangular',
    minimum: 100,
    mostLikely: 150,
    maximum: 220,
    mean: null,
    standardDeviation: null,
    probability: null,
    impact: null,
    lambdaShape: null,
    category: 'Ingénierie',
    unit: 'MAD',
    enabled: true,
    notes: '',
  }],
  correlations: { mode: 'independent', names: [], values: [] },
};

export const simulationFixture: SimulationResponse = {
  project: { name: 'Projet test', analysisType: 'cost', unit: 'EUR', baseline: 1000 },
  run: {
    simulations: 1000,
    seed: 42,
    confidenceLevels: [0.5, 0.8, 0.9, 0.95],
    correlationsEnabled: false,
    generatedAt: '2026-08-21T10:00:00Z',
  },
  summary: { mean: 1120, std: 95, minimum: 810, maximum: 1450 },
  percentiles: [
    { percentile: 'P50', amount: 1100, recommended_reserve: 100 },
    { percentile: 'P80', amount: 1210, recommended_reserve: 210 },
    { percentile: 'P90', amount: 1280, recommended_reserve: 280 },
    { percentile: 'P95', amount: 1340, recommended_reserve: 340 },
  ],
  sensitivity: [
    { item_name: 'Études', spearman_rho: 0.72 },
    { item_name: 'Fournisseur', spearman_rho: -0.31 },
  ],
  convergence: [
    { draw_count: 500, target_percentile: 'P90', relative_change: 0.02, stop_recommended: false },
    { draw_count: 1000, target_percentile: 'P90', relative_change: 0.004, stop_recommended: true },
  ],
  baselineComparison: [{ baseline: 1000, simulated_mean: 1120, exceedance_probability: 0.78 }],
  correlationDiagnostics: [],
  histogram: [
    { start: 800, end: 1000, count: 130 },
    { start: 1000, end: 1200, count: 530 },
    { start: 1200, end: 1400, count: 340 },
  ],
  sCurve: [
    { amount: 810, probability: 0 },
    { amount: 1100, probability: 0.5 },
    { amount: 1280, probability: 0.9 },
    { amount: 1450, probability: 1 },
  ],
};
