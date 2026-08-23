import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { CheckCircle2, CloudUpload, FolderOpen, Trash2, Users, XCircle } from 'lucide-react';
import { Button, Card, CardTitle, StatusPill } from '../common';
import {
  deleteSharedRegister,
  listSharedRegisters,
  saveSharedRegister,
} from '../../services/sharedProjects';
import { useAuth } from '../../state/AuthContext';
import type { RiskRegisterDraft, SharedRegister } from '../../types';

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('fr-FR');
}

type Props = {
  register: RiskRegisterDraft;
  canPublish: boolean;
  onOpen: (shared: SharedRegister) => void;
  /** Publishing also attaches the draft to that shared register. */
  onPublished: (registerId: number) => void;
};

/**
 * The shared shelf: every register held by the installation, open to everyone.
 * This is what replaces mailing spreadsheets between colleagues.
 */
export function SharedRegisters({ register, canPublish, onOpen, onPublished }: Props) {
  const { user } = useAuth();
  const [shared, setShared] = useState<SharedRegister[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [name, setName] = useState('');
  const [overwriteId, setOverwriteId] = useState<number | ''>('');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setShared(await listSharedRegisters());
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Les registres partagés sont indisponibles.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  useEffect(() => {
    // Pre-fill with the project name so publishing is one click in the common case.
    setName((current) => current || register.metadata.projectName);
  }, [register.metadata.projectName]);

  const publish = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setPublishing(true);
    try {
      const stored = await saveSharedRegister(
        name,
        register,
        overwriteId === '' ? undefined : overwriteId,
      );
      setMessage(
        overwriteId === ''
          ? `« ${stored.name} » est désormais partagé avec l’équipe.`
          : `« ${stored.name} » a été mis à jour pour toute l’équipe.`,
      );
      onPublished(stored.id);
      setOverwriteId('');
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'L’enregistrement a échoué.');
    } finally {
      setPublishing(false);
    }
  };

  const remove = async (target: SharedRegister) => {
    setError('');
    setMessage('');
    try {
      await deleteSharedRegister(target.id);
      setMessage(`« ${target.name} » a été retiré. Les exécutions produites sont conservées.`);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La suppression a échoué.');
    }
  };

  return (
    <Card className="register-builder-card shared-registers-card">
      <CardTitle info={false}>
        <span className="title-with-icon"><Users />Registres partagés</span>
      </CardTitle>
      <p className="builder-intro">
        Tout membre connecté voit ces registres et peut reprendre le travail d’un collègue. L’auteur
        de chaque enregistrement est conservé.
      </p>

      {message ? <div className="pro-success-banner"><CheckCircle2 />{message}</div> : null}
      {error ? <div className="pro-error-banner register-banner" role="alert"><XCircle />{error}</div> : null}

      <form className="shared-publish-form" onSubmit={publish}>
        <label>Nom du registre
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label>Enregistrer
          <select
            value={overwriteId}
            onChange={(event) => setOverwriteId(event.target.value === '' ? '' : Number(event.target.value))}
          >
            <option value="">comme un nouveau registre</option>
            {shared.map((item) => (
              <option key={item.id} value={item.id}>en remplaçant « {item.name} »</option>
            ))}
          </select>
        </label>
        <Button variant="primary" type="submit" disabled={publishing || !canPublish}
          title={canPublish ? undefined : 'Complétez le projet et ses postes avant de partager.'}>
          <CloudUpload />{publishing ? 'Enregistrement…' : 'Partager'}
        </Button>
      </form>

      {loading ? <p className="builder-intro">Chargement…</p> : null}
      {!loading && !shared.length ? (
        <p className="note">Aucun registre partagé pour le moment.</p>
      ) : null}

      {shared.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Registre</th><th>Créé par</th><th>Dernière modification</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {shared.map((item) => (
                <tr key={item.id}>
                  <td><b>{item.name}</b></td>
                  <td>{item.createdBy.fullName}</td>
                  <td>
                    {item.updatedBy.fullName}
                    <br /><small>{formatDate(item.updatedAt)}</small>
                  </td>
                  <td>
                    <div className="admin-row-actions">
                      <Button onClick={() => onOpen(item)}><FolderOpen />Ouvrir</Button>
                      {user?.role === 'admin' ? (
                        <Button aria-label={`Supprimer ${item.name}`} onClick={() => void remove(item)}>
                          <Trash2 />
                        </Button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {user?.role === 'admin' ? null : (
        <p className="note">
          <StatusPill tone="gray">Membre</StatusPill> La suppression d’un registre partagé est
          réservée aux administrateurs.
        </p>
      )}
    </Card>
  );
}
