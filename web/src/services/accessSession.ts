const ACCESS_STORAGE_KEY = 'risksim.access.v1';
const ACCESS_HEADER = 'X-Access-Key';

/** Fired when the API rejects the stored key, so the interface can lock itself again. */
export const UNAUTHORIZED_EVENT = 'risksim:unauthorized';

type StoredAccess = { version: 1; key: string };

export class AccessDeniedError extends Error {
  constructor(message = 'Clé d’accès absente ou invalide.') {
    super(message);
    this.name = 'AccessDeniedError';
  }
}

/**
 * The shared secret lives in sessionStorage: it disappears when the tab closes,
 * and it never has to be baked into the built bundle.
 */
export function readAccessKey(): string | null {
  try {
    const raw = window.sessionStorage.getItem(ACCESS_STORAGE_KEY);
    if (!raw) return null;
    const stored = JSON.parse(raw) as StoredAccess;
    return stored.version === 1 && stored.key ? stored.key : null;
  } catch {
    window.sessionStorage.removeItem(ACCESS_STORAGE_KEY);
    return null;
  }
}

export function storeAccessKey(key: string | null): void {
  try {
    if (key) {
      const stored: StoredAccess = { version: 1, key };
      window.sessionStorage.setItem(ACCESS_STORAGE_KEY, JSON.stringify(stored));
    } else {
      window.sessionStorage.removeItem(ACCESS_STORAGE_KEY);
    }
  } catch {
    /* storage unavailable: the key simply is not remembered across reloads */
  }
}

function headersWithAccessKey(init?: HeadersInit, key?: string | null): Headers {
  const headers = new Headers(init);
  const accessKey = key === undefined ? readAccessKey() : key;
  if (accessKey) headers.set(ACCESS_HEADER, accessKey);
  return headers;
}

/**
 * Same contract as `fetch`, with the shared key attached. A 401 means the key
 * is gone or was revoked: drop it and let the interface show the gate again.
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(path, { ...init, headers: headersWithAccessKey(init.headers) });
  if (response.status === 401) {
    storeAccessKey(null);
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new AccessDeniedError(payload?.detail);
  }
  return response;
}

export type AccessProbe = { gateEnabled: boolean };

/** Ask the public health endpoint whether this deployment is gated at all. */
export async function probeAccessControl(): Promise<AccessProbe> {
  const response = await fetch('/api/health');
  if (!response.ok) throw new Error(`Le service est injoignable (${response.status}).`);
  const payload = await response.json() as { accessControl?: string };
  return { gateEnabled: payload.accessControl === 'enabled' };
}

/** Check a candidate key against the API without running any simulation. */
export async function verifyAccessKey(key: string): Promise<boolean> {
  const response = await fetch('/api/session', { headers: headersWithAccessKey(undefined, key) });
  if (response.status === 401) return false;
  if (!response.ok) throw new Error(`La vérification a échoué (${response.status}).`);
  return true;
}
