import { useState, type FormEvent } from 'react';
import { CheckCircle2, KeyRound, ShieldCheck, XCircle } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { changeOwnPassword } from '../../services/authSession';
import { useAuth } from '../../state/AuthContext';

function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).slice(0, 2);
  return parts.map((part) => part[0]?.toUpperCase() ?? '').join('') || '··';
}

function formatDate(value: string | null): string {
  if (!value) return 'Jamais';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('fr-FR');
}

export function ProfilePage() {
  const { user } = useAuth();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  if (!user) return null;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage('');
    setError('');
    if (next !== confirmation) {
      setError('Les deux saisies du nouveau mot de passe diffèrent.');
      return;
    }
    setBusy(true);
    try {
      await changeOwnPassword(current, next);
      setMessage('Votre mot de passe a été changé. Vos autres navigateurs ont été déconnectés.');
      setCurrent('');
      setNext('');
      setConfirmation('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Le changement a échoué.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Profil et sécurité"
        subtitle="Votre compte sur cette installation."
      />

      {message ? <div className="pro-success-banner"><CheckCircle2 />{message}</div> : null}
      {error ? <div className="pro-error-banner register-banner" role="alert"><XCircle />{error}</div> : null}

      <div className="profile-layout">
        <Card className="identity-card">
          <div className="identity-header">
            <div className="profile-avatar large">{initials(user.fullName)}</div>
            <div>
              <h2>{user.fullName}</h2>
              <p>{user.role === 'admin' ? 'Administrateur' : 'Membre'}</p>
              <StatusPill tone={user.isActive ? 'green' : 'gray'}>
                {user.isActive ? 'Compte actif' : 'Compte désactivé'}
              </StatusPill>
            </div>
          </div>
          <dl>
            <div><dt>Adresse e-mail</dt><dd>{user.email}</dd></div>
            <div><dt>Compte créé</dt><dd>{formatDate(user.createdAt)}</dd></div>
            <div><dt>Dernière connexion</dt><dd>{formatDate(user.lastLoginAt)}</dd></div>
          </dl>
        </Card>

        <Card className="security-score-card">
          <ShieldCheck />
          <div>
            <span>Où vivent vos données</span>
            <strong>Sur cette machine</strong>
            <small>
              L’installation est locale au réseau de l’entreprise. Les comptes et les sessions sont
              stockés dans une base locale ; rien n’est envoyé à l’extérieur.
            </small>
          </div>
        </Card>
      </div>

      <Card className="register-builder-card">
        <CardTitle info={false}><span className="title-with-icon"><KeyRound />Changer le mot de passe</span></CardTitle>
        <form className="pro-form-grid register-project-form" onSubmit={submit}>
          <label className="wide">Mot de passe actuel
            <input
              type="password"
              value={current}
              onChange={(event) => setCurrent(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <label>Nouveau mot de passe
            <input
              type="password"
              value={next}
              onChange={(event) => setNext(event.target.value)}
              autoComplete="new-password"
              minLength={10}
              required
            />
          </label>
          <label>Confirmer le nouveau mot de passe
            <input
              type="password"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              autoComplete="new-password"
              minLength={10}
              required
            />
          </label>
          <div className="builder-footer wide">
            <span>Au moins 10 caractères. Vos sessions ouvertes ailleurs seront fermées.</span>
            <Button variant="primary" type="submit" disabled={busy}>
              {busy ? 'Changement…' : 'Changer le mot de passe'}
            </Button>
          </div>
        </form>
      </Card>
    </>
  );
}
