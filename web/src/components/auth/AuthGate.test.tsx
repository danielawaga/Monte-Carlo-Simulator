import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthGate } from './AuthGate';
import { AuthProvider } from '../../state/AuthContext';
import { simulationService } from '../../services/simulationService';

type Reply = { status: number; body?: unknown };

function stubApi(routes: Record<string, (init?: RequestInit) => Reply>) {
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

const AWA = {
  id: 1,
  email: 'awa@exemple.fr',
  fullName: 'Awa Diallo',
  role: 'admin' as const,
  isActive: true,
  createdAt: '2026-08-23T04:00:00Z',
  lastLoginAt: null,
};

function renderGate() {
  return render(
    <AuthProvider>
      <AuthGate><p>Contenu protégé</p></AuthGate>
    </AuthProvider>,
  );
}

describe('AuthGate', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('propose la première configuration sur une installation vierge', async () => {
    const user = userEvent.setup();
    let created = false;
    stubApi({
      '/api/health': () => ({ status: 200, body: { setupRequired: !created, authenticated: created } }),
      '/api/setup': () => {
        created = true;
        return { status: 200, body: { user: AWA } };
      },
    });

    renderGate();

    expect(await screen.findByRole('heading', { name: 'Première configuration' })).toBeVisible();
    expect(screen.queryByText('Contenu protégé')).toBeNull();

    await user.type(screen.getByLabelText('Nom complet'), 'Awa Diallo');
    await user.type(screen.getByLabelText('Adresse e-mail'), 'awa@exemple.fr');
    await user.type(screen.getByLabelText('Mot de passe'), 'motdepasse-solide');
    await user.click(screen.getByRole('button', { name: 'Créer le compte administrateur' }));

    expect(await screen.findByText('Contenu protégé')).toBeVisible();
  });

  it('demande une connexion quand des comptes existent déjà', async () => {
    const user = userEvent.setup();
    stubApi({
      '/api/health': () => ({ status: 200, body: { setupRequired: false, authenticated: false } }),
      '/api/auth/login': (init) => {
        const body = JSON.parse(String(init?.body ?? '{}')) as { password?: string };
        return body.password === 'motdepasse-solide'
          ? { status: 200, body: { user: AWA } }
          : { status: 401, body: { detail: 'Identifiants invalides.' } };
      },
    });

    renderGate();

    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeVisible();
    expect(screen.queryByLabelText('Nom complet')).toBeNull();

    await user.type(screen.getByLabelText('Adresse e-mail'), 'awa@exemple.fr');
    await user.type(screen.getByLabelText('Mot de passe'), 'mauvais');
    await user.click(screen.getByRole('button', { name: 'Se connecter' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Identifiants invalides.');
    expect(screen.queryByText('Contenu protégé')).toBeNull();

    await user.clear(screen.getByLabelText('Mot de passe'));
    await user.type(screen.getByLabelText('Mot de passe'), 'motdepasse-solide');
    await user.click(screen.getByRole('button', { name: 'Se connecter' }));

    expect(await screen.findByText('Contenu protégé')).toBeVisible();
  });

  it('reprend une session déjà ouverte sans redemander les identifiants', async () => {
    stubApi({
      '/api/health': () => ({ status: 200, body: { setupRequired: false, authenticated: true } }),
      '/api/auth/me': () => ({ status: 200, body: { user: AWA } }),
    });

    renderGate();

    expect(await screen.findByText('Contenu protégé')).toBeVisible();
  });

  it('reverrouille l’interface quand l’API rejette la session en cours', async () => {
    stubApi({
      '/api/health': () => ({ status: 200, body: { setupRequired: false, authenticated: true } }),
      '/api/auth/me': () => ({ status: 200, body: { user: AWA } }),
      '/api/register/validate': () => ({ status: 401, body: { detail: 'Authentification requise.' } }),
    });

    renderGate();
    expect(await screen.findByText('Contenu protégé')).toBeVisible();

    await expect(simulationService.validateRegister({} as never)).rejects.toThrow(
      'Authentification requise.',
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Connexion' })).toBeVisible());
    expect(screen.queryByText('Contenu protégé')).toBeNull();
  });

  it('propose de réessayer quand le moteur est injoignable', async () => {
    stubApi({ '/api/health': () => ({ status: 503 }) });

    renderGate();

    expect(await screen.findByText('Service injoignable')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeVisible();
  });
});
