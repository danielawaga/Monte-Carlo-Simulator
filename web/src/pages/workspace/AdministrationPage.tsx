import { useState, type FormEvent } from 'react';
import { History, KeyRound, ShieldCheck, UserPlus, Users, X } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { auditEvents, teamMembers } from '../../data/workspaceData';

export function AdministrationPage() {
  const [members, setMembers] = useState(teamMembers);
  const [showInvite, setShowInvite] = useState(false);

  const inviteMember = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get('name'));
    setMembers((current) => [...current, {
      initials: name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase(),
      name,
      email: String(form.get('email')),
      role: String(form.get('role')),
      scope: String(form.get('scope')),
      mfa: false,
      lastSeen: 'Invitation envoyée',
      status: 'En attente',
    }]);
    setShowInvite(false);
  };

  const updateRole = (email: string, role: string) => setMembers((current) => current.map((member) => member.email === email ? { ...member, role } : member));

  return (
    <>
      <PageHeader
        title="Administration de l’espace"
        subtitle="Utilisateurs, rôles, sécurité et piste d’audit du Projet Atlas."
        actions={<Button variant="primary" onClick={() => setShowInvite(true)}><UserPlus />Inviter un membre</Button>}
      />

      <div className="admin-kpis">
        <Card><Users /><div><span>Utilisateurs</span><b>{members.length}</b><small>4 actifs · 1 suspendu</small></div></Card>
        <Card><ShieldCheck /><div><span>Couverture MFA</span><b>80 %</b><small>1 compte à sécuriser</small></div></Card>
        <Card><KeyRound /><div><span>Administrateurs</span><b>1</b><small>Revue trimestrielle conforme</small></div></Card>
        <Card><History /><div><span>Événements d’audit</span><b>128</b><small>Sur les 30 derniers jours</small></div></Card>
      </div>

      {showInvite ? (
        <Card className="pro-editor-card">
          <CardTitle info={false} action={<Button aria-label="Fermer le formulaire" onClick={() => setShowInvite(false)}><X /></Button>}>Inviter un membre</CardTitle>
          <form className="invite-form" onSubmit={inviteMember}>
            <label>Nom complet<input name="name" required /></label><label>Adresse e-mail<input name="email" type="email" required /></label>
            <label>Rôle<select name="role" defaultValue="Contributeur"><option>Administrateur</option><option>Risk manager</option><option>Analyste</option><option>Contributeur</option><option>Lecteur</option></select></label>
            <label>Périmètre<input name="scope" defaultValue="Projet Atlas" required /></label>
            <div><Button type="button" onClick={() => setShowInvite(false)}>Annuler</Button><Button type="submit" variant="primary">Envoyer l’invitation</Button></div>
          </form>
        </Card>
      ) : null}

      <Card className="pro-admin-table">
        <CardTitle info={false}>Membres et habilitations</CardTitle>
        <div className="table-wrap"><table className="pro-table"><thead><tr><th>Utilisateur</th><th>Rôle</th><th>Périmètre</th><th>Dernière activité</th><th>MFA</th><th>Statut</th></tr></thead><tbody>{members.map((member) => <tr key={member.email}><td><div className="member-cell"><span>{member.initials}</span><div><b>{member.name}</b><small>{member.email}</small></div></div></td><td><select aria-label={`Rôle de ${member.name}`} value={member.role} onChange={(event) => updateRole(member.email, event.target.value)}><option>Administrateur</option><option>Risk manager</option><option>Analyste</option><option>Contributeur</option><option>Lecteur</option></select></td><td>{member.scope}</td><td>{member.lastSeen}</td><td><StatusPill tone={member.mfa ? 'green' : 'orange'}>{member.mfa ? 'Activée' : 'À activer'}</StatusPill></td><td><StatusPill tone={member.status === 'Actif' ? 'green' : member.status === 'Suspendu' ? 'gray' : 'blue'}>{member.status}</StatusPill></td></tr>)}</tbody></table></div>
      </Card>

      <div className="pro-admin-grid">
        <Card className="pro-panel">
          <CardTitle info={false}>Matrice des responsabilités</CardTitle>
          <div className="role-matrix">
            <div><b>Administrateur</b><span>Paramètres, sécurité, membres et intégrations.</span><StatusPill tone="red">Accès sensible</StatusPill></div>
            <div><b>Risk manager</b><span>Registre, scénarios, validation et rapports.</span><StatusPill tone="orange">Validation</StatusPill></div>
            <div><b>Analyste</b><span>Configuration, exécution et analyse des simulations.</span><StatusPill tone="blue">Production</StatusPill></div>
            <div><b>Lecteur</b><span>Consultation des résultats approuvés uniquement.</span><StatusPill tone="gray">Lecture</StatusPill></div>
          </div>
        </Card>
        <Card className="pro-panel">
          <CardTitle info={false}>Activité récente</CardTitle>
          <ol className="audit-list">{auditEvents.map((event) => <li key={`${event.at}-${event.actor}`}><i /><div><b>{event.action}</b><span>{event.object}</span><small>{event.actor} · {event.at}</small></div></li>)}</ol>
        </Card>
      </div>
    </>
  );
}
