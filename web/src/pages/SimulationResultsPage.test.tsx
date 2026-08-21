import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SimulationProvider } from '../state/SimulationContext';
import { simulationFixture } from '../test/simulationFixture';
import { SimulationResultsPage } from './SimulationResultsPage';

function renderResults() {
  window.sessionStorage.setItem(
    'risksim.result.v1',
    JSON.stringify({ version: 1, result: simulationFixture }),
  );
  return render(
    <MemoryRouter initialEntries={['/resultats']}>
      <SimulationProvider><SimulationResultsPage /></SimulationProvider>
    </MemoryRouter>,
  );
}

describe('SimulationResultsPage', () => {
  beforeEach(() => {
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:results');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
  });

  it('affiche les résultats réels et permet de parcourir les visualisations', async () => {
    const user = userEvent.setup();
    renderResults();

    expect(screen.getByRole('heading', { name: 'Résultats de la simulation' })).toBeVisible();
    expect(screen.getByText('Projet test')).toBeVisible();
    expect(screen.getAllByText('1 210 EUR')).toHaveLength(2);

    await user.click(screen.getByRole('tab', { name: 'Distribution' }));
    expect(screen.getByRole('img', { name: /Histogramme réel/i })).toBeVisible();

    await user.click(screen.getByRole('tab', { name: 'S-curve' }));
    expect(screen.getByRole('img', { name: 'Courbe cumulative réelle' })).toBeVisible();

    await user.click(screen.getByRole('tab', { name: 'Sensibilité' }));
    expect(screen.getByRole('img', { name: 'Diagramme Tornado des postes les plus sensibles' })).toBeVisible();

    await user.click(screen.getByRole('tab', { name: 'Robustesse' }));
    expect(screen.getByText('Convergence stabilisée')).toBeVisible();
  });

  it('exporte un classeur complet et décrit honnêtement la copie de l’adresse', async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(new Blob(['xlsx']), { status: 200 }),
    );
    const clipboardWrite = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: clipboardWrite },
    });
    renderResults();

    await user.click(screen.getByRole('button', { name: /Exporter Excel/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/results/export');
    expect(options?.method).toBe('POST');
    expect(JSON.parse(String(options?.body))).toMatchObject({
      result: { project: { name: 'Projet test' }, run: { seed: 42 } },
      config: { simulations: 50000 },
    });
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /Télécharger le dossier ZIP/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[1][0]).toBe('/api/results/export-bundle');

    await user.click(screen.getByRole('button', { name: 'Copier l’adresse' }));
    expect(clipboardWrite).toHaveBeenCalledWith(window.location.href);
    expect(screen.getByRole('status')).toHaveTextContent(
      'Pour transmettre les données de la simulation, partagez plutôt le fichier Excel exporté.',
    );
  });
});
