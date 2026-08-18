import { useState, type FormEvent } from 'react';
import { CheckCircle2, KeyRound, Laptop, LockKeyhole, Save, ShieldCheck, Smartphone } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';

export function ProfilePage() {
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [secondarySessionRevoked, setSecondarySessionRevoked] = useState(false);
  const [passwordEditing, setPasswordEditing] = useState(false);
  const [securityMessage, setSecurityMessage] = useState('');

  const saveProfile = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setEditing(false);
    setSaved(true);
  };

  return (
    <>
      <PageHeader
        title="Profil et sécurité"
        subtitle="Informations professionnelles, préférences personnelles et sécurité du compte."
        actions={editing ? null : <Button variant="primary" onClick={() => { setEditing(true); setSaved(false); }}>Modifier le profil</Button>}
      />

      {saved ? <div className="pro-success-banner"><CheckCircle2 />Votre profil a été mis à jour.</div> : null}

      <div className="profile-layout">
        <Card className="identity-card">
          <div className="identity-header"><div className="profile-avatar large">PD</div><div><h2>Pierre Dubois</h2><p>Directeur de programme · Administrateur</p><StatusPill>Compte actif</StatusPill></div></div>
          <dl><div><dt>Organisation</dt><dd>Programme Atlas</dd></div><div><dt>Périmètre</dt><dd>Tous les projets</dd></div><div><dt>Compte créé</dt><dd>12 janvier 2026</dd></div><div><dt>Dernière connexion</dt><dd>17 août 2026 · 21:48</dd></div></dl>
        </Card>

        <Card className="security-score-card">
          <ShieldCheck /><div><span>Niveau de sécurité</span><strong>Élevé</strong><small>4 contrôles sur 4 sont conformes.</small></div>
          <ul><li><CheckCircle2 />Authentification multifacteur</li><li><CheckCircle2 />Mot de passe conforme</li><li><CheckCircle2 />Adresse e-mail vérifiée</li><li><CheckCircle2 />Sessions récentes contrôlées</li></ul>
        </Card>
      </div>

      <form className="profile-details-form" onSubmit={saveProfile}>
        <Card className="pro-settings-card">
          <CardTitle info={false}>Informations professionnelles</CardTitle>
          <div className="pro-form-grid">
            <label>Prénom<input defaultValue="Pierre" disabled={!editing} /></label><label>Nom<input defaultValue="Dubois" disabled={!editing} /></label>
            <label>Fonction<input defaultValue="Directeur de programme" disabled={!editing} /></label><label>Département<input defaultValue="Transformation & Risques" disabled={!editing} /></label>
            <label>Adresse e-mail<input type="email" defaultValue="pierre.dubois@atlas-programme.ma" disabled={!editing} /></label><label>Téléphone<input defaultValue="+212 6 12 34 56 78" disabled={!editing} /></label>
            <label>Langue<select defaultValue="fr" disabled={!editing}><option value="fr">Français</option><option value="en">English</option></select></label><label>Fuseau horaire<select defaultValue="Africa/Casablanca" disabled={!editing}><option>Africa/Casablanca</option><option>Europe/Paris</option><option>UTC</option></select></label>
          </div>
          {editing ? <div className="form-inline-actions"><Button type="button" onClick={() => setEditing(false)}>Annuler</Button><Button variant="primary" type="submit"><Save />Enregistrer</Button></div> : null}
        </Card>
      </form>

      <div className="pro-security-grid">
        <Card className="pro-panel">
          <CardTitle info={false}><span className="title-with-icon"><LockKeyhole />Authentification</span></CardTitle>
          <div className="security-setting"><div><b>Mot de passe</b><span>Modifié il y a 34 jours · Conforme à la politique</span></div><Button onClick={() => { setPasswordEditing(true); setSecurityMessage(''); }}>Modifier</Button></div>
          {passwordEditing ? <form className="security-password-form" onSubmit={(event) => { event.preventDefault(); setPasswordEditing(false); setSecurityMessage('Mot de passe mis à jour. Les autres sessions devront se reconnecter.'); }}><label>Mot de passe actuel<input type="password" required autoComplete="current-password" /></label><label>Nouveau mot de passe<input type="password" required minLength={12} autoComplete="new-password" /></label><div><Button type="button" onClick={() => setPasswordEditing(false)}>Annuler</Button><Button variant="primary" type="submit">Mettre à jour</Button></div></form> : null}
          <div className="security-setting"><div><b>Authentification multifacteur</b><span>Application d’authentification configurée</span></div><StatusPill>Activée</StatusPill></div>
          <div className="security-setting"><div><b>Codes de récupération</b><span>8 codes disponibles · Générés le 12/01/2026</span></div><Button onClick={() => setSecurityMessage('8 nouveaux codes de récupération ont été générés et les anciens invalidés.')}><KeyRound />Régénérer</Button></div>
          {securityMessage ? <div className="pro-inline-confirmation"><CheckCircle2 />{securityMessage}</div> : null}
        </Card>

        <Card className="pro-panel">
          <CardTitle info={false}>Sessions actives</CardTitle>
          <div className="session-row"><Laptop /><div><b>Chrome · Casablanca</b><span>Linux · session actuelle</span><small>Dernière activité : maintenant</small></div><StatusPill>Actuelle</StatusPill></div>
          {secondarySessionRevoked ? null : <div className="session-row"><Smartphone /><div><b>Safari · Rabat</b><span>iPhone · 196.70.xxx.xxx</span><small>Dernière activité : 16/08/2026 à 09:12</small></div><Button onClick={() => setSecondarySessionRevoked(true)}>Révoquer</Button></div>}
          {secondarySessionRevoked ? <div className="pro-inline-confirmation"><CheckCircle2 />Session mobile révoquée.</div> : null}
        </Card>
      </div>
    </>
  );
}
