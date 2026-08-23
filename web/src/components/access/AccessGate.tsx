import { useState, type FormEvent, type ReactNode } from 'react';
import { LockKeyhole, ShieldAlert } from 'lucide-react';
import { Button } from '../common';
import { useAccess } from '../../state/AccessContext';

/** Holds the interface back until the shared access key has been accepted. */
export function AccessGate({ children }: { children: ReactNode }) {
  const { status, error, unlock, retry } = useAccess();
  const [key, setKey] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (status === 'open' || status === 'unlocked') return <>{children}</>;

  if (status === 'checking') {
    return (
      <div className="access-gate">
        <p className="access-checking" role="status">Vérification de l’accès…</p>
      </div>
    );
  }

  if (status === 'unavailable') {
    return (
      <div className="access-gate">
        <section className="access-card">
          <ShieldAlert className="access-icon" />
          <h1>Service injoignable</h1>
          <p>{error || 'Le moteur de simulation ne répond pas.'}</p>
          <Button variant="primary" onClick={retry}>Réessayer</Button>
        </section>
      </div>
    );
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    const opened = await unlock(key);
    setSubmitting(false);
    if (opened) setKey('');
  };

  return (
    <div className="access-gate">
      <form className="access-card" onSubmit={submit}>
        <LockKeyhole className="access-icon" />
        <h1>Accès protégé</h1>
        <p>
          Cet espace héberge des registres de risques confidentiels. Saisissez la clé d’accès
          partagée fournie par l’administrateur.
        </p>
        <label htmlFor="access-key">Clé d’accès</label>
        <input
          id="access-key"
          type="password"
          autoComplete="current-password"
          value={key}
          onChange={(event) => setKey(event.target.value)}
          autoFocus
        />
        {error ? <p className="access-error" role="alert">{error}</p> : null}
        <Button variant="primary" type="submit" disabled={submitting}>
          {submitting ? 'Vérification…' : 'Déverrouiller'}
        </Button>
      </form>
    </div>
  );
}
