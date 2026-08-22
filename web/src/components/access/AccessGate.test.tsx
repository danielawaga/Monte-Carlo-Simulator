import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccessGate } from './AccessGate';
import { AccessProvider } from '../../state/AccessContext';
import { simulationService } from '../../services/simulationService';

type Route = { status: number; body?: unknown };

function stubApi(routes: Record<string, (init?: RequestInit) => Route>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    const route = routes[path];
    if (!route) throw new Error(`Route non simulée : ${path}`);
    const { status, body } = route(init);
    return new Response(JSON.stringify(body ?? {}), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function readKey(init?: RequestInit) {
  return new Headers(init?.headers).get('X-Access-Key');
}

function renderGate() {
  return render(
    <AccessProvider>
      <AccessGate><p>Contenu protégé</p></AccessGate>
    </AccessProvider>,
  );
}

describe('AccessGate', () => {
  beforeEach(() => window.sessionStorage.clear());
  afterEach(() => vi.unstubAllGlobals());

  it('laisse passer quand le déploiement n’est pas protégé', async () => {
    stubApi({ '/api/health': () => ({ status: 200, body: { accessControl: 'disabled' } }) });

    renderGate();

    expect(await screen.findByText('Contenu protégé')).toBeVisible();
  });

  it('demande la clé, la vérifie et la mémorise pour les appels suivants', async () => {
    const user = userEvent.setup();
    stubApi({
      '/api/health': () => ({ status: 200, body: { accessControl: 'enabled' } }),
      '/api/session': (init) =>
        readKey(init) === 'bonne-cle'
          ? { status: 200, body: { authenticated: true } }
          : { status: 401, body: { detail: 'Clé d’accès absente ou invalide.' } },
    });

    renderGate();

    const field = await screen.findByLabelText('Clé d’accès');
    expect(screen.queryByText('Contenu protégé')).toBeNull();

    await user.type(field, 'mauvaise-cle');
    await user.click(screen.getByRole('button', { name: 'Déverrouiller' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Clé d’accès invalide.');
    expect(screen.queryByText('Contenu protégé')).toBeNull();

    await user.clear(screen.getByLabelText('Clé d’accès'));
    await user.type(screen.getByLabelText('Clé d’accès'), 'bonne-cle');
    await user.click(screen.getByRole('button', { name: 'Déverrouiller' }));

    expect(await screen.findByText('Contenu protégé')).toBeVisible();
    expect(JSON.parse(String(window.sessionStorage.getItem('risksim.access.v1')))).toEqual({
      version: 1,
      key: 'bonne-cle',
    });
  });

  it('réutilise la clé stockée sans redemander la saisie', async () => {
    window.sessionStorage.setItem(
      'risksim.access.v1',
      JSON.stringify({ version: 1, key: 'bonne-cle' }),
    );
    stubApi({
      '/api/health': () => ({ status: 200, body: { accessControl: 'enabled' } }),
      '/api/session': (init) =>
        readKey(init) === 'bonne-cle' ? { status: 200 } : { status: 401 },
    });

    renderGate();

    expect(await screen.findByText('Contenu protégé')).toBeVisible();
  });

  it('reverrouille l’interface quand l’API rejette la clé en cours de session', async () => {
    window.sessionStorage.setItem(
      'risksim.access.v1',
      JSON.stringify({ version: 1, key: 'cle-revoquee' }),
    );
    stubApi({
      '/api/health': () => ({ status: 200, body: { accessControl: 'enabled' } }),
      '/api/session': () => ({ status: 200 }),
      '/api/register/validate': () => ({ status: 401, body: { detail: 'Clé révoquée.' } }),
    });

    renderGate();
    expect(await screen.findByText('Contenu protégé')).toBeVisible();

    await expect(
      simulationService.validateRegister({} as never),
    ).rejects.toThrow('Clé révoquée.');

    await waitFor(() => expect(screen.getByLabelText('Clé d’accès')).toBeVisible());
    expect(window.sessionStorage.getItem('risksim.access.v1')).toBeNull();
    expect(screen.queryByText('Contenu protégé')).toBeNull();
  });

  it('propose de réessayer quand le service est injoignable', async () => {
    stubApi({ '/api/health': () => ({ status: 503 }) });

    renderGate();

    expect(await screen.findByText('Service injoignable')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeVisible();
  });
});
