import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Play, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { portfolioRisks, simulationRuns } from '../../data/workspaceData';

const budgetPositions = [
  { label: 'Budget de référence', value: '2,10 M€', width: 34, tone: 'baseline' },
  { label: 'Coût moyen simulé', value: '2,45 M€', width: 40, tone: 'mean' },
  { label: 'Engagement P80', value: '4,12 M€', width: 67, tone: 'p80' },
  { label: 'Exposition P90', value: '6,24 M€', width: 100, tone: 'p90' },
];

const categoryExposure = [
  { label: 'Technique & données', amount: '136 k€', width: 100, tone: 'orange' },
  { label: 'Gouvernance & conformité', amount: '108 k€', width: 79, tone: 'blue' },
  { label: 'Ressources & organisation', amount: '80 k€', width: 59, tone: 'green' },
  { label: 'Fournisseurs & finances', amount: '72 k€', width: 53, tone: 'gray' },
];

function KpiTile({ label, value, detail, trend, tone = 'blue' }: { label: string; value: string; detail: string; trend: string; tone?: string }) {
  return (
    <Card className="pro-kpi">
      <div className={`pro-kpi-accent ${tone}`} />
      <span>{label}</span><strong>{value}</strong><small>{detail}</small><em>{trend}</em>
    </Card>
  );
}

export function DashboardPage() {
  const criticalRisks = portfolioRisks.filter(({ level }) => level === 'Critique' || level === 'Élevé').length;

  return (
    <>
      <PageHeader
        title="Pilotage du portefeuille de risques"
        subtitle="Projet Atlas — Modernisation du système d’information"
        actions={<Link className="button primary" to="/configuration"><Play />Lancer une simulation</Link>}
      />

      <div className="pro-context-bar">
        <div><span>Référence de gouvernance</span><b>Comité des risques · Août 2026</b></div>
        <div><span>Date d’arrêté</span><b>17 août 2026</b></div>
        <div><span>Qualité des données</span><b className="positive-text"><CheckCircle2 />94 % conformes</b></div>
        <div><span>Prochaine revue</span><b>21 août 2026 · 09:00</b></div>
      </div>

      <div className="pro-kpi-grid">
        <KpiTile label="Budget de référence" value="2,10 M€" detail="Version approuvée V3.2" trend="Inchangé depuis le 31/07" tone="navy" />
        <KpiTile label="Coût moyen simulé" value="2,45 M€" detail="50 000 itérations" trend="+2,5 % vs. comité précédent" tone="blue" />
        <KpiTile label="Réserve recommandée P80" value="2,02 M€" detail="Engagement total : 4,12 M€" trend="−70 k€ après mitigation" tone="orange" />
        <KpiTile label="Risques prioritaires" value={String(criticalRisks)} detail="1 critique · 4 élevés" trend="2 décisions attendues cette semaine" tone="red" />
      </div>

      <div className="pro-dashboard-grid">
        <Card className="pro-panel">
          <CardTitle info={false}>Positionnement budgétaire</CardTitle>
          <p className="pro-card-subtitle">Lecture consolidée de la dernière simulation validée.</p>
          <div className="budget-position">
            {budgetPositions.map((item) => (
              <div className="budget-row" key={item.label}>
                <div><span>{item.label}</span><b>{item.value}</b></div>
                <div className="budget-track"><i className={item.tone} style={{ width: `${item.width}%` }} /></div>
              </div>
            ))}
          </div>
          <div className="pro-callout warning"><AlertTriangle /><div><b>Décision budgétaire requise</b><span>Le budget approuvé couvre 34 % de l’exposition P90. La réserve P80 doit être arbitrée avant le 28 août.</span></div></div>
        </Card>

        <Card className="pro-panel">
          <CardTitle info={false}>Exposition agrégée par domaine</CardTitle>
          <p className="pro-card-subtitle">Exposition brute calculée par probabilité × impact.</p>
          <div className="exposure-list">
            {categoryExposure.map((item) => (
              <div key={item.label}><span>{item.label}</span><div><i className={item.tone} style={{ width: `${item.width}%` }} /></div><b>{item.amount}</b></div>
            ))}
          </div>
          <Link className="pro-inline-link" to="/risques">Examiner le registre complet <ArrowRight /></Link>
        </Card>
      </div>

      <div className="pro-dashboard-grid lower">
        <Card className="pro-panel pro-runs">
          <CardTitle info={false} action={<Link className="pro-inline-link" to="/resultats">Ouvrir l’analyse <ArrowRight /></Link>}>Dernières simulations</CardTitle>
          <div className="table-wrap">
            <table className="pro-table">
              <thead><tr><th>Exécution</th><th>Scénario</th><th>Itérations</th><th>Moyenne</th><th>P80</th><th>Statut</th></tr></thead>
              <tbody>{simulationRuns.slice(0, 3).map((run) => <tr key={run.id}><td><b>{run.id}</b><small>{run.executedAt}</small></td><td>{run.scenario}<small>{run.author}</small></td><td>{run.iterations}</td><td>{run.mean}</td><td>{run.p80}</td><td><StatusPill tone={run.status === 'Validée' ? 'green' : run.status === 'À approuver' ? 'orange' : 'gray'}>{run.status}</StatusPill></td></tr>)}</tbody>
            </table>
          </div>
        </Card>

        <Card className="pro-panel decisions-panel">
          <CardTitle info={false}>Décisions et échéances</CardTitle>
          <ul className="decision-list">
            <li><span className="decision-icon urgent"><AlertTriangle /></span><div><b>Valider le plan de succession de l’architecte</b><small>Responsable : Pierre Dubois · Échéance 20/08</small></div></li>
            <li><span className="decision-icon"><Clock3 /></span><div><b>Arbitrer la réserve budgétaire P80</b><small>Comité de pilotage · Échéance 28/08</small></div></li>
            <li><span className="decision-icon safe"><ShieldCheck /></span><div><b>Approuver le scénario Mitigation v2</b><small>Risk manager · Revue prête</small></div></li>
          </ul>
        </Card>
      </div>
    </>
  );
}
