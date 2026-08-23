import type { AuthUser, HealthStatus, NewUserInput, UserUpdate } from '../types';

/** Fired when the API rejects the session, so the interface can return to sign-in. */
export const UNAUTHENTICATED_EVENT = 'risksim:unauthenticated';

export class UnauthenticatedError extends Error {
  constructor(message = 'Authentification requise.') {
    super(message);
    this.name = 'UnauthenticatedError';
  }
}

async function detail(response: Response, fallback: string): Promise<string> {
  const payload = await response.json().catch(() => null) as { detail?: string } | null;
  return payload?.detail ?? fallback;
}

/**
 * Same contract as `fetch`. The session travels in an httpOnly cookie the page
 * cannot read, so nothing is attached by hand — the browser does it. A 401 means
 * the session is gone or was revoked: tell the interface to lock itself again.
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(path, { ...init, credentials: 'same-origin' });
  if (response.status === 401) {
    window.dispatchEvent(new Event(UNAUTHENTICATED_EVENT));
    throw new UnauthenticatedError(await detail(response, 'Authentification requise.'));
  }
  return response;
}

/**
 * For the public endpoints only — setup and sign-in — where a 401 means "wrong
 * credentials" rather than "your session ended". Authenticated calls must go
 * through `apiFetch`, which relocks the interface on 401.
 */
async function postPublicJson<T>(path: string, body: unknown, fallback: string): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await detail(response, fallback));
  return response.json() as Promise<T>;
}

async function postAuthenticated(path: string, body: unknown, fallback: string): Promise<void> {
  const response = await apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await detail(response, fallback));
}

/** Ask the public health endpoint what the interface should show first. */
export async function readHealth(): Promise<HealthStatus> {
  const response = await fetch('/api/health', { credentials: 'same-origin' });
  if (!response.ok) throw new Error(`Le service est injoignable (${response.status}).`);
  const payload = await response.json() as { setupRequired?: boolean; authenticated?: boolean };
  return {
    setupRequired: payload.setupRequired === true,
    authenticated: payload.authenticated === true,
  };
}

export async function createFirstAdmin(
  input: { email: string; fullName: string; password: string },
): Promise<AuthUser> {
  const payload = await postPublicJson<{ user: AuthUser }>('/api/setup', input, 'L’initialisation a échoué.');
  return payload.user;
}

export async function signIn(email: string, password: string): Promise<AuthUser> {
  const payload = await postPublicJson<{ user: AuthUser }>(
    '/api/auth/login',
    { email, password },
    'La connexion a échoué.',
  );
  return payload.user;
}

export async function signOut(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
}

export async function readCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error(`La session n’a pas pu être vérifiée (${response.status}).`);
  const payload = await response.json() as { user: AuthUser };
  return payload.user;
}

export async function changeOwnPassword(currentPassword: string, newPassword: string): Promise<void> {
  await postAuthenticated(
    '/api/account/password',
    { currentPassword, newPassword },
    'Le changement a échoué.',
  );
}

export async function listUsers(): Promise<AuthUser[]> {
  const response = await apiFetch('/api/users');
  if (!response.ok) throw new Error(await detail(response, 'La liste des comptes est indisponible.'));
  const payload = await response.json() as { users: AuthUser[] };
  return payload.users;
}

export async function createUser(input: NewUserInput): Promise<AuthUser> {
  const response = await apiFetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error(await detail(response, 'La création du compte a échoué.'));
  const payload = await response.json() as { user: AuthUser };
  return payload.user;
}

export async function updateUser(id: number, update: UserUpdate): Promise<AuthUser> {
  const response = await apiFetch(`/api/users/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  });
  if (!response.ok) throw new Error(await detail(response, 'La mise à jour a échoué.'));
  const payload = await response.json() as { user: AuthUser };
  return payload.user;
}
