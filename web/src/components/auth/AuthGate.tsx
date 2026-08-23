import { useState, type FormEvent, type ReactNode } from 'react';
import { LockKeyhole, ServerCog, ShieldAlert } from 'lucide-react';
import { Button } from '../common';
import { useAuth } from '../../state/AuthContext';

/** Holds the interface back until somebody is signed in. */
export function AuthGate({ children }: { children: ReactNode }) {
  const { status, error, signIn, createAdmin, retry } = useAuth();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  if (status === 'signedIn') return <>{children}</>;

  if (status === 'checking') {
    return (
      <div className="auth-gate">
        <p className="auth-checking" role="status">Vérification de la session…</p>
      </div>
    );
  }

  if (status === 'unreachable') {
    return (
      <div className="auth-gate">
        <section className="auth-card">
          <ShieldAlert className="auth-icon" />
          <h1>Service injoignable</h1>
          <p>{error || 'Le moteur de simulation ne répond pas.'}</p>
          <Button variant="primary" onClick={retry}>Réessayer</Button>
        </section>
      </div>
    );
  }

  const isSetup = status === 'setup';

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    const done = isSetup
      ? await createAdmin({ email, fullName, password })
      : await signIn(email, password);
    setBusy(false);
    if (done) {
      setPassword('');
      setFullName('');
    }
  };

  return (
    <div className="auth-gate">
      <form className="auth-card" onSubmit={submit}>
        {isSetup ? <ServerCog className="auth-icon" /> : <LockKeyhole className="auth-icon" />}
        <h1>{isSetup ? 'Première configuration' : 'Connexion'}</h1>
        <p>
          {isSetup
            ? 'Cette installation ne contient aucun compte. Créez le compte administrateur ; cet écran ne réapparaîtra plus ensuite.'
            : 'Cet espace héberge des registres de risques confidentiels. Identifiez-vous pour continuer.'}
        </p>

        {isSetup ? (
          <>
            <label htmlFor="auth-name">Nom complet</label>
            <input
              id="auth-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              autoComplete="name"
              required
            />
          </>
        ) : null}

        <label htmlFor="auth-email">Adresse e-mail</label>
        <input
          id="auth-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="username"
          required
          autoFocus
        />

        <label htmlFor="auth-password">Mot de passe</label>
        <input
          id="auth-password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete={isSetup ? 'new-password' : 'current-password'}
          required
        />
        {isSetup ? <small>Au moins 10 caractères.</small> : null}

        {error ? <p className="auth-error" role="alert">{error}</p> : null}

        <Button variant="primary" type="submit" disabled={busy}>
          {busy ? 'Veuillez patienter…' : isSetup ? 'Créer le compte administrateur' : 'Se connecter'}
        </Button>
      </form>
    </div>
  );
}
