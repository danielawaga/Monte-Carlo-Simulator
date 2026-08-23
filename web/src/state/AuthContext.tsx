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
  UNAUTHENTICATED_EVENT,
  createFirstAdmin,
  readCurrentUser,
  readHealth,
  signIn,
  signOut,
} from '../services/authSession';
import type { AuthUser } from '../types';

/**
 * `setup` — a brand-new installation with no account yet.
 * `signedOut` — accounts exist and nobody is signed in on this browser.
 * `signedIn` — a session is open.
 * `unreachable` — the engine did not answer, so the state is unknown.
 */
export type AuthStatus = 'checking' | 'setup' | 'signedOut' | 'signedIn' | 'unreachable';

type AuthState = {
  status: AuthStatus;
  user: AuthUser | null;
  error: string;
  signIn: (email: string, password: string) => Promise<boolean>;
  createAdmin: (input: { email: string; fullName: string; password: string }) => Promise<boolean>;
  signOut: () => Promise<void>;
  retry: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('checking');
  const [user, setUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus('checking');
    setError('');

    void (async () => {
      try {
        const health = await readHealth();
        if (cancelled) return;
        if (health.setupRequired) {
          setUser(null);
          setStatus('setup');
          return;
        }
        const current = health.authenticated ? await readCurrentUser() : null;
        if (cancelled) return;
        setUser(current);
        setStatus(current ? 'signedIn' : 'signedOut');
      } catch (cause) {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : 'Le service est injoignable.');
        setStatus('unreachable');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [attempt]);

  useEffect(() => {
    const onRejected = () => {
      setUser(null);
      setError('Votre session a expiré, connectez-vous à nouveau.');
      setStatus('signedOut');
    };
    window.addEventListener(UNAUTHENTICATED_EVENT, onRejected);
    return () => window.removeEventListener(UNAUTHENTICATED_EVENT, onRejected);
  }, []);

  const handleSignIn = useCallback(async (email: string, password: string) => {
    try {
      setUser(await signIn(email, password));
      setError('');
      setStatus('signedIn');
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La connexion a échoué.');
      return false;
    }
  }, []);

  const createAdmin = useCallback(
    async (input: { email: string; fullName: string; password: string }) => {
      try {
        setUser(await createFirstAdmin(input));
        setError('');
        setStatus('signedIn');
        return true;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : 'L’initialisation a échoué.');
        return false;
      }
    },
    [],
  );

  const handleSignOut = useCallback(async () => {
    await signOut();
    setUser(null);
    setError('');
    setStatus('signedOut');
  }, []);

  const retry = useCallback(() => setAttempt((current) => current + 1), []);

  const value = useMemo(
    () => ({
      status,
      user,
      error,
      signIn: handleSignIn,
      createAdmin,
      signOut: handleSignOut,
      retry,
    }),
    [createAdmin, error, handleSignIn, handleSignOut, retry, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth doit être utilisé dans AuthProvider');
  return value;
}
