import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DashboardPage } from './DashboardPage';
import type { SavedRegister, SavedRun } from '../../types';

const REGISTER = {
  id: 1,
  name: 'Extension usine',
  register: { items: [{ id: 'risk-1' }, { id: 'risk-2' }] },
  createdAt: '2026-08-01T09:00:00Z',
  updatedAt: '2026-08-02T09:00:00Z',
} as unknown as SavedRegister;

const RUN = {
  id: 7,
  registerId: 1,
  label: 'Décision P80',
  config: {},
  createdAt: '2026-08-03T09:00:00Z',
  result: {
    project: { name: 'Extension usine', analysisType: 'cost', unit: 'EUR', baseline: 100_000 },
    run: { simulations: 50_000, seed: 42, confidenceLevels: [80], correlationsEnabled: false, generatedAt: '' },
    summary: { mean: 106_844 },
    percentiles: [
      { percentile: 'P80', amount: 123_978, recommended_reserve: 23_978 },
      { percentile: 'P90', amount: 138_376, recommended_reserve: 38_376 },
    ],
    sensitivity: [
      { item_name: 'Études', spearman_rho: 0.69 },
      { item_name: 'Fournitures', spearman_rho: -0.31 },
    ],
    convergence: [], baselineComparison: [], correlationDiagnostics: [], histogram: [], sCurve: [],
  },
} as unknown as SavedRun;

function answer(registers: SavedRegister[], runs: SavedRun[]) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
    const url = String(input);
    const body = url.includes('/api/runs') ? { runs } : { registers };
    return Promise.resolve(new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }));
  });
}

/** La locale française sépare les milliers par une espace fine insécable
 *  (U+202F). Plutôt que de dépendre de la façon dont chaque comparateur la
 *  normalise, on retire toutes les espaces des deux côtés. */
function shownAmount(value: number) {
  const target = `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} EUR`;
  const strip = (text: string) => text.replace(/\s/gu, '');
  return strip(document.body.textContent ?? '').includes(strip(target));
}

function renderDashboard() {
  return render(<MemoryRouter initialEntries={['/']}><DashboardPage /></MemoryRouter>);
}

describe('DashboardPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('n’invente rien quand la base locale est vide', async () => {
    answer([], []);
    renderDashboard();

    expect(await screen.findByRole('heading', { name: 'Aucune donnée sur ce poste' })).toBeVisible();
    expect(screen.getByRole('link', { name: /Préparer un registre de risques/ })).toBeVisible();
  });

  it('affiche les chiffres de la dernière exécution conservée', async () => {
    answer([REGISTER], [RUN]);
    renderDashboard();

    // Les montants viennent du résultat stocké, pas d'un jeu de démonstration.
    await screen.findByText('Postes les plus influents');
    expect(shownAmount(106_844), 'moyenne de l’exécution').toBe(true);
    expect(shownAmount(123_978), 'P80').toBe(true);
    expect(shownAmount(138_376), 'P90').toBe(true);
    expect(shownAmount(23_978), 'réserve recommandée P80').toBe(true);

    // Le classement de sensibilité est celui du moteur, trié par influence absolue.
    const contributors = screen.getAllByText(/Études|Fournitures/);
    expect(contributors[0]).toHaveTextContent('Études');

    // L'exécution est rattachée à son registre : le nom paraît dans le tableau
    // des exécutions et dans la liste des registres.
    expect(screen.getAllByText('Extension usine')).toHaveLength(2);
    expect(screen.getByText(/2 postes · modifié le 02\/08\/2026/)).toBeVisible();
  });

  it('signale une base illisible au lieu de faire semblant', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Base verrouillée.'));
    renderDashboard();

    expect(await screen.findByRole('heading', { name: 'Base locale illisible' })).toBeVisible();
    expect(screen.getByText('Base verrouillée.')).toBeVisible();
  });
});
