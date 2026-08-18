import { useState, type FormEvent } from 'react';
import { Bell, Database, Globe2, Save, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';

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
      <PageHeader title="Paramètres du projet" subtitle="Référentiel de calcul, gouvernance des données et règles de notification." />
      <form className="pro-settings-layout" onSubmit={saveSettings} onChange={() => setSaved(false)}>
        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><Globe2 />Identité et contexte du projet</span></CardTitle>
          <div className="pro-form-grid">
            <label className="wide">Nom du projet<input defaultValue="Projet Atlas — Modernisation du SI" /></label>
            <label>Code projet<input defaultValue="ATL-SI-2026" /></label>
            <label>Devise de référence<select defaultValue="EUR"><option value="EUR">Euro (EUR)</option><option value="MAD">Dirham marocain (MAD)</option><option value="USD">Dollar américain (USD)</option></select></label>
            <label>Fuseau horaire<select defaultValue="Africa/Casablanca"><option>Africa/Casablanca</option><option>Europe/Paris</option><option>UTC</option></select></label>
            <label>Date d’arrêté<input type="date" defaultValue="2026-08-17" /></label>
            <label className="wide">Description<textarea defaultValue="Programme de modernisation des applications cœur et de migration des données historiques." /></label>
          </div>
        </Card>

        <Card className="pro-settings-card">
          <CardTitle info={false}><span className="title-with-icon"><SlidersHorizontal />Standards de modélisation</span></CardTitle>
          <div className="pro-form-grid">
            <label>Itérations par défaut<select defaultValue="50000"><option value="10000">10 000</option><option value="50000">50 000</option><option value="100000">100 000</option></select></label>
            <label>Méthode d’échantillonnage<select defaultValue="lhs"><option value="lhs">Latin Hypercube</option><option value="random">Pseudo-aléatoire</option></select></label>
            <label>Niveau d’engagement<select defaultValue="80"><option value="75">P75</option><option value="80">P80</option><option value="90">P90</option></select></label>
            <label>Seuil de dépassement (€)<input type="number" defaultValue="5000000" step="100000" /></label>
            <label>Seuil de convergence<select defaultValue="1"><option value="0.5">0,5 %</option><option value="1">1 %</option><option value="2">2 %</option></select></label>
            <label>Politique de corrélation<select defaultValue="explicit"><option value="explicit">Matrice explicite requise</option><option value="independent">Indépendance par défaut</option></select></label>
          </div>
          <div className="pro-policy-note"><ShieldCheck /><span><b>Contrôle de gouvernance actif</b> Toute modification de ces paramètres invalide les simulations précédemment approuvées.</span></div>
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
