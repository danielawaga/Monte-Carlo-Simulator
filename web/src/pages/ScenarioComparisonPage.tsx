import { CheckCircle2, Download, FolderOpen, TrendingDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../components/common';
import { Metric } from '../components/cards/StatCard';
import { SCurveCard } from '../components/charts/Charts';
import { comparison, risks, scenarios } from '../data/mockSimulation';

export function ScenarioComparisonPage() {
  const exportReport = () => {
    const rows = [['Indicateur', 'Référence', 'Mitigation', 'Écart', 'Variation'], ...comparison];
    const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(';')).join('\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'comparaison-scenarios-atlas.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <PageHeader
        title="Comparaison de scénarios"
        subtitle="Évaluation de l’efficacité financière du plan de mitigation v2."
        actions={<Link className="button secondary" to="/configuration"><FolderOpen />Créer un scénario</Link>}
      />

      <div className="scenario-governance-bar">
        <div><span>Comparaison</span><b>CMP-260816-02</b></div><div><span>Référence</span><b>SIM-260816-03</b></div><div><span>Mitigation</span><b>SIM-260816-02</b></div><div><span>Jeu de données</span><b>Registre v2026.08.16</b></div><div><span>Lecture</span><StatusPill tone="blue">Écart favorable</StatusPill></div>
      </div>

      <div className="scenario-tools">
        <div>{scenarios.map((scenario) => <div key={scenario.name} className="scenario-select scenario-summary"><i className={scenario.color} /><span><b>{scenario.name}</b><small>{scenario.description}</small></span><CheckCircle2 /></div>)}</div>
      </div>
      <div className="scenario-cards">
        {scenarios.map((scenario) => <Card key={scenario.name}><CardTitle info={false}>{scenario.name}　<StatusPill tone={scenario.color === 'blue' ? 'green' : 'orange'}>{scenario.color === 'blue' ? 'Validé' : 'À approuver'}</StatusPill></CardTitle><div className="metrics"><Metric label="P80" value={scenario.p80} sub="Engagement à 80 %" /><Metric label="P90" value={scenario.p90} sub="Exposition à 90 %" /><Metric label="Réserve recommandée (P80)" value={scenario.reserve} sub="Écart au budget de référence" /></div></Card>)}
      </div>
      <div className="comparison-main">
        <SCurveCard comparison />
        <Card>
          <CardTitle>Synthèse comparative</CardTitle>
          <table><thead><tr><th>Indicateur</th><th>Référence</th><th>Mitigation</th><th>Écart</th><th>Variation</th></tr></thead><tbody>{comparison.map((row) => <tr key={row[0]}>{row.map((value, index) => <td key={`${row[0]}-${index}`} className={index === 4 ? 'positive' : ''}>{value}{index === 4 ? ' ↓' : ''}</td>)}</tr>)}</tbody></table>
          <p className="note">Les écarts en vert réduisent l’exposition. Le scénario Mitigation doit être approuvé avant utilisation dans le reporting exécutif.</p>
        </Card>
      </div>
      <Card className="contributions">
        <CardTitle>Principaux facteurs d’impact (sensibilité)</CardTitle>
        <table><thead><tr><th>Risque</th><th>Référence</th><th>Mitigation</th><th>Évolution de la contribution</th></tr></thead><tbody>{risks.map((risk, index) => <tr key={risk.id}><td><b>{risk.id}</b>　{risk.risk}</td><td><span className="bar blue" style={{ width: `${145 - index * 18}px` }} /> {24 - index * 4} %　 {risk.coefficient}</td><td><span className="bar green" style={{ width: `${100 - index * 13}px` }} /> {16 - index * 2} %</td><td>−{index + 2} pts　<TrendingDown /></td></tr>)}</tbody></table>
        <div className="card-footer"><Link className="button secondary" to="/risques">Examiner le registre</Link><Button onClick={exportReport}><Download />Exporter la comparaison</Button></div>
      </Card>
    </>
  );
}
