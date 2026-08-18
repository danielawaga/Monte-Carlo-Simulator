import { useState } from 'react';
import { CheckCircle2, Copy, Download, Info, Share2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../components/common';
import { StatCard } from '../components/cards/StatCard';
import { HistogramCard, SCurveCard } from '../components/charts/Charts';
import { risks, summary } from '../data/mockSimulation';

export function SimulationResultsPage() {
  const [shareState, setShareState] = useState<'idle' | 'copied' | 'error'>('idle');
  const sorted = [risks[3], risks[0], risks[4], risks[1], risks[2]];

  const exportResults = () => {
    const rows = [
      ['Indicateur', 'Valeur'],
      ['Simulation', 'SIM-260816-03'],
      ['Moyenne', summary.mean],
      ['P80', summary.p80],
      ['P90', summary.p90],
      ['Probabilité de dépassement de 5 M€', summary.exceedance],
      ['Réserve recommandée P80', summary.reserve],
    ];
    const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(';')).join('\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'resultats-SIM-260816-03.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareResults = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShareState('copied');
    } catch {
      setShareState('error');
    }
  };

  return (
    <>
      <PageHeader
        title="Résultats de la simulation"
        subtitle="Analyse probabiliste validée du scénario de référence."
        actions={<><Button onClick={exportResults}><Download />Exporter les résultats</Button><Button onClick={shareResults}>{shareState === 'copied' ? <CheckCircle2 /> : shareState === 'error' ? <Copy /> : <Share2 />}{shareState === 'copied' ? 'Lien copié' : shareState === 'error' ? 'Copier manuellement' : 'Partager'}</Button></>}
      />

      <div className="result-governance-bar">
        <div><span>Identifiant</span><b>SIM-260816-03</b></div><div><span>Scénario</span><b>Référence validée</b></div><div><span>Exécution</span><b>16/08/2026 · 18:42</b></div><div><span>Convergence</span><b className="positive-text"><CheckCircle2 />0,42 %</b></div><div><span>Validation</span><StatusPill>Approuvée</StatusPill></div>
      </div>

      <div className="kpi-grid">
        <StatCard label="Moyenne" value={summary.mean} icon="money" />
        <StatCard label="P80" value={summary.p80} />
        <StatCard label="P90" value={summary.p90} />
        <StatCard label="Probabilité de dépassement" value={summary.exceedance} sub="Au-delà de 5 000 000 €" icon="alert" />
      </div>
      <div className="results-main">
        <HistogramCard />
        <div className="side-stats">
          <StatCard label="Budget de référence" value={summary.baseline} sub="Version budgétaire V3.2" />
          <StatCard label="Réserve recommandée (P80)" value={summary.reserve} sub="Engagement total : 4 120 000 €" icon="shield" />
          <StatCard label="Simulations effectuées" value="50 000" sub="Graine reproductible : 20260816" icon="money" />
        </div>
      </div>
      <div className="results-bottom">
        <SCurveCard />
        <Card>
          <CardTitle>Top 5 des risques par sensibilité (Spearman)</CardTitle>
          <table><thead><tr><th>#</th><th>Risque</th><th>Coefficient</th><th>Impact</th></tr></thead><tbody>{sorted.map((risk, index) => <tr key={risk.id}><td>{index + 1}</td><td><b>{risk.id}</b>　{risk.risk}</td><td>{risk.coefficient}</td><td><StatusPill tone={risk.level === 'Élevé' ? 'orange' : risk.level === 'Faible' ? 'green' : 'blue'}>{risk.level}</StatusPill></td></tr>)}</tbody></table>
          <p className="note">Les coefficients sont calculés sur les 50 000 itérations. Une valeur absolue élevée indique un levier prioritaire de mitigation.</p>
        </Card>
      </div>
      <div className="helpbar"><span><Info />Résultats reproductibles avec la graine 20260816 et le registre version 2026.08.16.</span><span><Link to="/aide">Consulter la méthode et les règles de lecture ↗</Link></span></div>
    </>
  );
}
