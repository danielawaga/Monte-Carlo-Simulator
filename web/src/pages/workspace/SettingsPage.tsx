import { useEffect, useState } from 'react';
import { Database, HardDrive, Monitor, Moon, Palette, ShieldAlert, Sun } from 'lucide-react';
import { Card, CardTitle, PageHeader } from '../../components/common';
import { readStorage } from '../../services/savedProjects';
import { useTheme, type ThemePreference } from '../../state/ThemeContext';
import type { StorageInfo } from '../../types';

/**
 * Only settings that do something.
 *
 * This page used to offer notification rules, a retention period, an
 * "immutable" audit log, export permissions and a classification level. None
 * of them were wired to anything — the save button flipped a boolean — and
 * several described the shared deployment that no longer exists. Promising
 * governance an application does not perform is worse than not offering it.
 */

const themes: { value: ThemePreference; label: string; hint: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Clair', hint: 'Fond blanc en permanence.', icon: Sun },
  { value: 'dark', label: 'Sombre', hint: 'Fond sombre en permanence.', icon: Moon },
  { value: 'system', label: 'Système', hint: 'Suit le réglage de Windows.', icon: Monitor },
];

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [storage, setStorage] = useState<StorageInfo | null>(null);
  const [storageError, setStorageError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    readStorage()
      .then((info) => { if (!cancelled) setStorage(info); })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setStorageError(cause instanceof Error ? cause.message : 'Emplacement indisponible.');
        }
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <>
      <PageHeader
        title="Paramètres"
        subtitle="Apparence de l’interface et emplacement des données de ce poste."
      />

      <div className="settings-layout">
        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><Palette />Apparence</span></CardTitle>
          <p className="pro-card-subtitle">Le choix est retenu sur ce poste et s’applique immédiatement.</p>
          <div className="theme-choice" role="radiogroup" aria-label="Thème de l’interface">
            {themes.map(({ value, label, hint, icon: Icon }) => (
              <button
                type="button"
                role="radio"
                aria-checked={theme === value}
                className={theme === value ? 'is-active' : ''}
                onClick={() => setTheme(value)}
                key={value}
              >
                <Icon /><b>{label}</b><small>{hint}</small>
              </button>
            ))}
          </div>
        </Card>

        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><Database />Données locales</span></CardTitle>
          <p className="pro-card-subtitle">
            Registres et historique vivent dans un seul fichier, sur cette machine. C’est le
            fichier à sauvegarder — rien ne circule sur le réseau.
          </p>
          {storageError !== null ? (
            <p className="panel-placeholder">{storageError}</p>
          ) : storage === null ? (
            <p className="panel-placeholder">Lecture…</p>
          ) : (
            <>
              <div className="storage-path">
                <HardDrive />
                <code>{storage.databasePath}</code>
              </div>
              <dl className="storage-counts">
                <div><dt>Registres enregistrés</dt><dd>{storage.registers}</dd></div>
                <div><dt>Simulations conservées</dt><dd>{storage.runs}</dd></div>
              </dl>
            </>
          )}
          <div className="pro-callout warning">
            <ShieldAlert />
            <div>
              <b>Ce fichier n’est pas chiffré</b>
              <span>
                Toute personne ouvrant la session Windows de ce poste peut le lire. Un écran de
                connexion n’y changerait rien : il protégerait l’interface, pas le fichier. Le
                chiffrement de disque, type BitLocker, est ce qui protège réellement des
                registres clients confidentiels.
              </span>
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}
