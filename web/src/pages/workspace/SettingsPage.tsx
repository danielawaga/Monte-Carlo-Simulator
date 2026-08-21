import { useState, type FormEvent } from 'react';
import { Bell, Database, Globe2, Save } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { useTheme, type ThemePreference } from '../../state/ThemeContext';

type NotificationKey = 'simulation' | 'criticalRisk' | 'approval' | 'weeklyReport';

function ToggleRow({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: () => void }) {
  return (
    <div className="pro-toggle-row">
      <div><b>{label}</b><span>{description}</span></div>
      <button className={`pro-switch ${checked ? 'on' : ''}`} type="button" role="switch" aria-checked={checked} onClick={onChange}><i /></button>
    </div>
  );
}

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [saved, setSaved] = useState(false);
  const [notifications, setNotifications] = useState<Record<NotificationKey, boolean>>({ simulation: true, criticalRisk: true, approval: true, weeklyReport: false });

  const toggleNotification = (key: NotificationKey) => {
    setNotifications((current) => ({ ...current, [key]: !current[key] }));
    setSaved(false);
  };

  const saveSettings = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaved(true);
  };

  return (
    <>
      <PageHeader title="Paramètres" subtitle="Préférences générales, gouvernance des données et règles de notification." />
      <form className="pro-settings-layout" onSubmit={saveSettings} onChange={() => setSaved(false)}>
        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><Globe2 />Préférences générales</span></CardTitle>
          <div className="pro-form-grid">
            <label>Fuseau horaire<select defaultValue="Africa/Casablanca"><option>Africa/Casablanca</option><option>Europe/Paris</option><option>UTC</option></select></label>
            <label>Langue de l’interface<select defaultValue="fr"><option value="fr">Français</option><option value="en">English</option></select></label>
            <label>Format des nombres<select defaultValue="fr-FR"><option value="fr-FR">1 234 567,89</option><option value="en-US">1,234,567.89</option></select></label>
            <label>Thème<select value={theme} onChange={(event) => setTheme(event.target.value as ThemePreference)}><option value="system">Système</option><option value="light">Clair</option><option value="dark">Sombre</option></select></label>
          </div>
        </Card>

        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><Bell />Notifications</span></CardTitle>
          <div className="pro-toggle-list">
            <ToggleRow label="Simulation terminée" description="Notifier l’initiateur et les validateurs." checked={notifications.simulation} onChange={() => toggleNotification('simulation')} />
            <ToggleRow label="Risque critique créé ou réévalué" description="Alerte immédiate aux membres du comité des risques." checked={notifications.criticalRisk} onChange={() => toggleNotification('criticalRisk')} />
            <ToggleRow label="Validation requise" description="Rappel après 24 heures sans décision." checked={notifications.approval} onChange={() => toggleNotification('approval')} />
            <ToggleRow label="Synthèse hebdomadaire" description="Rapport consolidé chaque lundi à 08:00." checked={notifications.weeklyReport} onChange={() => toggleNotification('weeklyReport')} />
          </div>
        </Card>

        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><Database />Conservation et traçabilité</span></CardTitle>
          <div className="pro-form-grid">
            <label>Durée de conservation<select defaultValue="7"><option value="3">3 ans</option><option value="7">7 ans</option><option value="10">10 ans</option></select></label>
            <label>Journal d’audit<select defaultValue="complete"><option value="complete">Complet et immuable</option><option value="standard">Standard</option></select></label>
            <label>Exports autorisés<select defaultValue="managers"><option value="managers">Administrateurs et risk managers</option><option value="all">Tous les membres</option></select></label>
            <label>Classification<select defaultValue="internal"><option value="internal">Interne confidentiel</option><option value="restricted">Restreint</option><option value="public">Public</option></select></label>
          </div>
        </Card>

        <div className="pro-sticky-actions">
          <span>Dernière modification par Pierre Dubois · 16/08/2026 à 17:21</span>
          <div>{saved ? <StatusPill>Paramètres enregistrés</StatusPill> : null}<Button variant="primary" type="submit"><Save />Enregistrer les paramètres</Button></div>
        </div>
      </form>
    </>
  );
}
