import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { CheckCircle2, ShieldCheck, UserPlus, Users, XCircle } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { createUser, listUsers, updateUser } from '../../services/authSession';
import { useAuth } from '../../state/AuthContext';
import type { AuthUser, UserRole } from '../../types';

const roleLabel: Record<UserRole, string> = { admin: 'Administrateur', member: 'Membre' };

function formatDate(value: string | null): string {
  if (!value) return 'Jamais';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('fr-FR');
}

export function AdministrationPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [inviting, setInviting] = useState(false);
  const [form, setForm] = useState({ email: '', fullName: '', password: '', role: 'member' as UserRole });

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setUsers(await listUsers());
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Les comptes sont indisponibles.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      const created = await createUser(form);
      setUsers((current) => [...current, created]);
      setMessage(`Le compte de ${created.fullName} a été créé.`);
      setForm({ email: '', fullName: '', password: '', role: 'member' });
      setInviting(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La création du compte a échoué.');
    }
  };

  const patch = async (target: AuthUser, update: { role?: UserRole; isActive?: boolean }) => {
    setError('');
    setMessage('');
    try {
      const updated = await updateUser(target.id, update);
      setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setMessage(`Le compte de ${updated.fullName} a été mis à jour.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La mise à jour a échoué.');
    }
  };

  const admins = users.filter((item) => item.role === 'admin' && item.isActive).length;

  if (currentUser && currentUser.role !== 'admin') {
    return (
      <>
        <PageHeader title="Administration" subtitle="Gestion des comptes de l’installation." />
        <Card className="register-builder-card">
          <div className="pro-empty-state">
            <ShieldCheck />
            <b>Réservé aux administrateurs</b>
            <span>Demandez à un administrateur de modifier les comptes.</span>
          </div>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Administration"
        subtitle="Comptes autorisés à utiliser cette installation."
        actions={
          inviting ? null : (
            <Button variant="primary" onClick={() => { setInviting(true); setMessage(''); }}>
              <UserPlus />Ajouter un membre
            </Button>
          )
        }
      />

      {message ? <div className="pro-success-banner"><CheckCircle2 />{message}</div> : null}
      {error ? <div className="pro-error-banner register-banner" role="alert"><XCircle />{error}</div> : null}

      <div className="admin-summary">
        <Card className="stat">
          <div className="stat-icon"><Users /></div>
          <div><label>Comptes</label><strong>{users.length}</strong><small>{users.filter((item) => item.isActive).length} actif(s)</small></div>
        </Card>
        <Card className="stat">
          <div className="stat-icon"><ShieldCheck /></div>
          <div><label>Administrateurs</label><strong>{admins}</strong><small>Le dernier ne peut être retiré</small></div>
        </Card>
      </div>

      {inviting ? (
        <Card className="register-builder-card">
          <CardTitle info={false}>Nouveau compte</CardTitle>
          <form className="pro-form-grid register-project-form" onSubmit={submit}>
            <label className="wide">Nom complet
              <input value={form.fullName} onChange={(event) => setForm({ ...form, fullName: event.target.value })} required />
            </label>
            <label>Adresse e-mail
              <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
            </label>
            <label>Rôle
              <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}>
                <option value="member">Membre</option>
                <option value="admin">Administrateur</option>
              </select>
            </label>
            <label>Mot de passe initial
              <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} minLength={10} required />
            </label>
            <div className="builder-footer wide">
              <span>Au moins 10 caractères. Le membre pourra le changer depuis son profil.</span>
              <div>
                <Button type="button" onClick={() => setInviting(false)}>Annuler</Button>
                <Button variant="primary" type="submit">Créer le compte</Button>
              </div>
            </div>
          </form>
        </Card>
      ) : null}

      <Card className="register-builder-card">
        <CardTitle info={false}>Membres et habilitations</CardTitle>
        {loading ? <p className="builder-intro">Chargement des comptes…</p> : null}
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Utilisateur</th><th>Rôle</th><th>Dernière connexion</th><th>Statut</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {users.map((item) => (
                <tr key={item.id}>
                  <td><b>{item.fullName}</b><br /><small>{item.email}</small></td>
                  <td>{roleLabel[item.role]}</td>
                  <td>{formatDate(item.lastLoginAt)}</td>
                  <td>
                    <StatusPill tone={item.isActive ? 'green' : 'gray'}>
                      {item.isActive ? 'Actif' : 'Désactivé'}
                    </StatusPill>
                  </td>
                  <td>
                    <div className="admin-row-actions">
                      <Button onClick={() => void patch(item, { role: item.role === 'admin' ? 'member' : 'admin' })}>
                        {item.role === 'admin' ? 'Rétrograder' : 'Promouvoir'}
                      </Button>
                      <Button onClick={() => void patch(item, { isActive: !item.isActive })}>
                        {item.isActive ? 'Désactiver' : 'Réactiver'}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && !users.length ? <p className="note">Aucun compte à afficher.</p> : null}
      </Card>
    </>
  );
}
