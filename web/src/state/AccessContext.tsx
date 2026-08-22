import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  UNAUTHORIZED_EVENT,
  probeAccessControl,
  readAccessKey,
  storeAccessKey,
  verifyAccessKey,
} from '../services/accessSession';

/**
 * `open` — this deployment runs without a shared key (local development).
 * `locked` — a key is required and we do not hold a valid one.
 * `unlocked` — the stored key was accepted by the API.
 * `unavailable` — the API could not be reached, so the gate state is unknown.
 */
export type AccessStatus = 'checking' | 'open' | 'locked' | 'unlocked' | 'unavailable';

type AccessState = {
  status: AccessStatus;
  error: string;
  gateEnabled: boolean;
  unlock: (key: string) => Promise<boolean>;
  lock: () => void;
  retry: () => void;
};

const AccessContext = createContext<AccessState | null>(null);

export function AccessProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AccessStatus>('checking');
  const [gateEnabled, setGateEnabled] = useState(false);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus('checking');
    setError('');

    void (async () => {
      try {
        const probe = await probeAccessControl();
        if (cancelled) return;
        setGateEnabled(probe.gateEnabled);
        if (!probe.gateEnabled) {
          storeAccessKey(null);
          setStatus('open');
          return;
        }
        const stored = readAccessKey();
        if (!stored) {
          setStatus('locked');
          return;
        }
        const valid = await verifyAccessKey(stored);
        if (cancelled) return;
        if (!valid) storeAccessKey(null);
        setStatus(valid ? 'unlocked' : 'locked');
      } catch (cause) {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : 'Le service est injoignable.');
        setStatus('unavailable');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [attempt]);

  useEffect(() => {
    const onUnauthorized = () => {
      setError('Votre session a expiré, saisissez à nouveau la clé d’accès.');
      setStatus('locked');
    };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const unlock = useCallback(async (key: string) => {
    const candidate = key.trim();
    if (!candidate) {
      setError('Saisissez la clé d’accès.');
      return false;
    }
    try {
      const valid = await verifyAccessKey(candidate);
      if (!valid) {
        setError('Clé d’accès invalide.');
        return false;
      }
      storeAccessKey(candidate);
      setError('');
      setStatus('unlocked');
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La vérification a échoué.');
      return false;
    }
  }, []);

  const lock = useCallback(() => {
    storeAccessKey(null);
    setError('');
    setStatus('locked');
  }, []);

  const retry = useCallback(() => setAttempt((current) => current + 1), []);

  const value = useMemo(
    () => ({ status, error, gateEnabled, unlock, lock, retry }),
    [error, gateEnabled, lock, retry, status, unlock],
  );

  return <AccessContext.Provider value={value}>{children}</AccessContext.Provider>;
}

export function useAccess() {
  const value = useContext(AccessContext);
  if (!value) throw new Error('useAccess doit être utilisé dans AccessProvider');
  return value;
}
