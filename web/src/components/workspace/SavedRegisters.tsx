import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { CheckCircle2, FolderOpen, Library, Save, Trash2, XCircle } from 'lucide-react';
import { Button, Card, CardTitle } from '../common';
import { deleteRegister, listRegisters, saveRegister } from '../../services/savedProjects';
import type { RiskRegisterDraft, SavedRegister } from '../../types';

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('fr-FR');
}

type Props = {
  register: RiskRegisterDraft;
  canPublish: boolean;
  onOpen: (shared: SavedRegister) => void;
  /** Saving also attaches the draft to that register, so runs link back to it. */
  onSaved: (registerId: number) => void;
};

/**
 * The local library: registers saved on this machine, with their run history.
 * Drafts used to live in localStorage, which vanishes with the browsing data.
 */
export function SavedRegisters({ register, canPublish, onOpen, onSaved }: Props) {
  const [shared, setShared] = useState<SavedRegister[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [name, setName] = useState('');
  const [overwriteId, setOverwriteId] = useState<number | ''>('');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setShared(await listRegisters());
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Les registres enregistrés sont indisponibles.');
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
      const stored = await saveRegister(
        name,
        register,
        overwriteId === '' ? undefined : overwriteId,
      );
      setMessage(
        overwriteId === ''
          ? `« ${stored.name} » a été enregistré.`
          : `« ${stored.name} » a été mis à jour.`,
      );
      onSaved(stored.id);
      setOverwriteId('');
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'L’enregistrement a échoué.');
    } finally {
      setPublishing(false);
    }
  };

  const remove = async (target: SavedRegister) => {
    setError('');
    setMessage('');
    try {
      await deleteRegister(target.id);
      setMessage(`« ${target.name} » a été retiré. Les simulations conservées le restent.`);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'La suppression a échoué.');
    }
  };

  return (
    <Card className="register-builder-card shared-registers-card">
      <CardTitle info={false}>
        <span className="title-with-icon"><Library />Registres enregistrés</span>
      </CardTitle>
      <p className="builder-intro">
        Vos registres sont conservés dans un fichier local, avec l’historique des simulations
        lancées depuis chacun. Rien ne quitte cette machine.
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
          title={canPublish ? undefined : 'Complétez le projet et ses postes avant d’enregistrer.'}>
          <Save />{publishing ? 'Enregistrement…' : 'Enregistrer'}
        </Button>
      </form>

      {loading ? <p className="builder-intro">Chargement…</p> : null}
      {!loading && !shared.length ? (
        <p className="note">Aucun registre enregistré pour le moment.</p>
      ) : null}

      {shared.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Registre</th><th>Créé le</th><th>Modifié le</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {shared.map((item) => (
                <tr key={item.id}>
                  <td><b>{item.name}</b></td>
                  <td><small>{formatDate(item.createdAt)}</small></td>
                  <td><small>{formatDate(item.updatedAt)}</small></td>
                  <td>
                    <div className="admin-row-actions">
                      <Button onClick={() => onOpen(item)}><FolderOpen />Ouvrir</Button>
                                              <Button aria-label={`Supprimer ${item.name}`} onClick={() => void remove(item)}>
                          <Trash2 />
                        </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

    </Card>
  );
}
