import { CheckCircle2, Download, FolderOpen, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { LiveSCurveCard } from '../components/charts/LiveCharts';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../components/common';
import { comparisonRows, formatAmount } from '../services/simulationMetrics';
import { useSimulation } from '../state/SimulationContext';

export function ScenarioComparisonPage() {
  const { result, reference, clearReference } = useSimulation();
  const sameScope = Boolean(
    result && reference
    && result.project.analysisType === reference.project.analysisType
    && result.project.unit === reference.project.unit,
  );
  const comparable = Boolean(result && reference && sameScope);
  const rows = result && reference && sameScope ? comparisonRows(reference, result) : [];
  const unit = result?.project.unit ?? reference?.project.unit ?? 'EUR';

  const exportReport = () => {
    const content = [
      ['Indicateur', 'Référence', 'Scénario courant', 'Écart', 'Variation'],
      ...rows.map((row) => [row.label, formatAmount(row.reference, unit), formatAmount(row.current, unit), formatAmount(row.difference, unit), row.variation]),
    ];
    const csv = content.map((row) => row.map((cell) => `"${cell}"`).join(';')).join('\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'comparaison-scenarios.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return <>
    <PageHeader title="Comparaison de scénarios" subtitle="Mesurez l’effet d’un jeu d’hypothèses sur les mêmes indicateurs probabilistes." actions={<Link className="button secondary" to="/configuration"><FolderOpen />Créer un scénario</Link>} />
    {!comparable ? <Card className="scenario-placeholder"><CardTitle>{result && reference && !sameScope ? 'Scénarios incompatibles' : 'Deux runs sont nécessaires'}</CardTitle><p>{result && reference && !sameScope ? `La référence (${reference.project.analysisType}, ${reference.project.unit}) ne peut pas être comparée au run courant (${result.project.analysisType}, ${result.project.unit}). Utilisez le même type d’analyse et la même unité.` : reference ? 'La référence est enregistrée. Lancez maintenant une nouvelle simulation depuis la configuration pour produire le scénario courant.' : 'Lancez une simulation, ouvrez les résultats et utilisez « Geler comme référence ». Modifiez ensuite le registre ou les hypothèses et relancez la simulation.'}</p><Link className="button primary" to={reference ? '/configuration' : '/resultats'}>{reference ? 'Configurer le scénario courant' : 'Accéder aux résultats'}</Link></Card> : <>
      <div className="scenario-governance-bar"><div><span>Référence</span><b>{reference?.project.name}</b></div><div><span>Scénario courant</span><b>{result?.project.name}</b></div><div><span>Unité</span><b>{unit}</b></div><div><span>Corrélations</span><b>{result?.run.correlationsEnabled ? 'Actives' : 'Non utilisées'}</b></div><div><span>Lecture</span><StatusPill tone="blue">Comparaison calculée</StatusPill></div></div>
      <div className="scenario-tools"><div><div className="scenario-select scenario-summary"><i className="blue" /><span><b>Référence</b><small>Graine {reference?.run.seed} · {reference?.run.simulations.toLocaleString('fr-FR')} tirages</small></span><CheckCircle2 /></div><div className="scenario-select scenario-summary"><i className="green" /><span><b>Scénario courant</b><small>Graine {result?.run.seed} · {result?.run.simulations.toLocaleString('fr-FR')} tirages</small></span><CheckCircle2 /></div></div></div>
      <div className="comparison-main"><LiveSCurveCard reference={reference} current={result!} /><Card><CardTitle>Synthèse comparative</CardTitle><table><thead><tr><th>Indicateur</th><th>Référence</th><th>Scénario courant</th><th>Écart</th><th>Variation</th></tr></thead><tbody>{rows.map((row) => <tr key={row.label}><td>{row.label}</td><td>{formatAmount(row.reference, unit)}</td><td>{formatAmount(row.current, unit)}</td><td>{formatAmount(row.difference, unit)}</td><td className={row.difference !== null && row.difference < 0 ? 'positive' : ''}>{row.variation}</td></tr>)}</tbody></table><p className="note">Un écart négatif indique une réduction de l’exposition pour les indicateurs de coût.</p></Card></div>
      <Card className="contributions"><CardTitle>Gouvernance de la référence</CardTitle><p className="note">La référence est conservée localement dans ce navigateur avec un schéma de stockage versionné. Elle peut être remplacée depuis la page Résultats.</p><div className="card-footer"><Button onClick={clearReference}><Trash2 />Supprimer la référence</Button><Button onClick={exportReport}><Download />Exporter la comparaison</Button></div></Card>
    </>}
  </>;
}
