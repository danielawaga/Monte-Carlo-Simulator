import { CheckCircle2, Copy, Download, Info, Save, Share2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { StatCard } from '../components/cards/StatCard';
import { HistogramCard, SCurveCard } from '../components/charts/Charts';
import { LiveHistogramCard, LiveSCurveCard } from '../components/charts/LiveCharts';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../components/common';
import { risks, summary as mockSummary } from '../data/mockSimulation';
import { formatAmount, numeric, percentile } from '../services/simulationMetrics';
import { useSimulation } from '../state/SimulationContext';

export function SimulationResultsPage() {
  const { result, reference, freezeReference } = useSimulation();
  const [shareState, setShareState] = useState<'idle' | 'copied' | 'error'>('idle');
  const liveSummary = useMemo(() => {
    if (!result) return null;
    const baseline = result.baselineComparison[0];
    const exceedance = numeric(baseline, 'exceedance_probability');
    return {
      mean: formatAmount(numeric(result.summary, 'mean'), result.project.unit),
      p80: formatAmount(numeric(percentile(result, 'P80'), 'amount'), result.project.unit),
      p90: formatAmount(numeric(percentile(result, 'P90'), 'amount'), result.project.unit),
      exceedance: exceedance === null ? 'Non disponible' : `${(exceedance * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`,
      baseline: formatAmount(result.project.baseline, result.project.unit),
      reserve: formatAmount(numeric(percentile(result, 'P80'), 'recommended_reserve'), result.project.unit),
    };
  }, [result]);
  const summary = liveSummary ?? mockSummary;
  const sensitivity = result?.sensitivity.slice(0, 5) ?? null;

  const exportResults = () => {
    const rows = [['Indicateur', 'Valeur'], ['Moyenne', summary.mean], ['P80', summary.p80], ['P90', summary.p90], ['Probabilité de dépassement', summary.exceedance], ['Réserve recommandée P80', summary.reserve]];
    const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(';')).join('\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'resultats-monte-carlo.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareResults = async () => {
    try { await navigator.clipboard.writeText(window.location.href); setShareState('copied'); }
    catch { setShareState('error'); }
  };

  return <>
    <PageHeader title="Résultats de la simulation" subtitle={result ? `Analyse réelle du projet ${result.project.name}.` : 'Données de démonstration — lancez une simulation pour obtenir les résultats réels.'} actions={<><Button onClick={exportResults}><Download />Exporter les résultats</Button>{result ? <Button onClick={freezeReference}><Save />{reference === result ? 'Référence enregistrée' : 'Geler comme référence'}</Button> : null}{result&&reference?<Link className="button secondary" to="/comparaison"><Copy/>Comparer à la référence</Link>:null}<Button onClick={shareResults}>{shareState === 'copied' ? <CheckCircle2 /> : shareState === 'error' ? <Copy /> : <Share2 />}{shareState === 'copied' ? 'Lien copié' : shareState === 'error' ? 'Copier manuellement' : 'Partager'}</Button></>} />

    <div className="result-governance-bar"><div><span>Projet</span><b>{result?.project.name ?? 'Projet Atlas'}</b></div><div><span>Source</span><b>{result ? 'Moteur Python' : 'Démonstration'}</b></div><div><span>Exécution</span><b>{result ? new Date(result.run.generatedAt).toLocaleString('fr-FR') : '16/08/2026 · 18:42'}</b></div><div><span>Corrélations</span><b className="positive-text"><CheckCircle2 />{result?.run.correlationsEnabled ? 'Actives' : 'Non utilisées'}</b></div><div><span>Validation</span><StatusPill>{result ? 'Calculée' : 'Démonstration'}</StatusPill></div></div>
    <div className="kpi-grid"><StatCard label="Moyenne" value={summary.mean} icon="money" /><StatCard label="P80" value={summary.p80} /><StatCard label="P90" value={summary.p90} /><StatCard label="Probabilité de dépassement" value={summary.exceedance} sub="Par rapport à la baseline" icon="alert" /></div>
    <div className="results-main">{result ? <LiveHistogramCard result={result} /> : <HistogramCard />}<div className="side-stats"><StatCard label="Budget de référence" value={summary.baseline} sub="Issu du registre Excel" /><StatCard label="Réserve recommandée (P80)" value={summary.reserve} sub="Écart positif à la baseline" icon="shield" /><StatCard label="Simulations effectuées" value={(result?.run.simulations ?? 50_000).toLocaleString('fr-FR')} sub={`Graine reproductible : ${result?.run.seed ?? 20260816}`} icon="money" /></div></div>
    <div className="results-bottom">{result ? <LiveSCurveCard current={result} /> : <SCurveCard />}<Card><CardTitle>Top 5 des risques par sensibilité (Spearman)</CardTitle><table><thead><tr><th>#</th><th>Risque</th><th>Coefficient</th><th>Direction</th></tr></thead><tbody>{sensitivity ? sensitivity.map((row, index) => <tr key={String(row.item_name)}><td>{index + 1}</td><td><b>{String(row.item_name)}</b></td><td>{typeof row.spearman_rho === 'number' ? row.spearman_rho.toLocaleString('fr-FR', { maximumFractionDigits: 3, signDisplay: 'always' }) : 'N/D'}</td><td><StatusPill tone={Number(row.spearman_rho) >= 0 ? 'orange' : 'blue'}>{String(row.direction)}</StatusPill></td></tr>) : [risks[3], risks[0], risks[4], risks[1], risks[2]].map((risk, index) => <tr key={risk.id}><td>{index + 1}</td><td><b>{risk.id}</b>　{risk.risk}</td><td>{risk.coefficient}</td><td><StatusPill tone="blue">{risk.level}</StatusPill></td></tr>)}</tbody></table><p className="note">Les coefficients proviennent des itérations du run courant. Une valeur absolue élevée indique un levier prioritaire de mitigation.</p></Card></div>
    <div className="helpbar"><span><Info />{result ? `Résultats reproductibles avec la graine ${result.run.seed}.` : 'Lancez une simulation réelle depuis la configuration.'}</span><span><Link to="/aide">Consulter la méthode et les règles de lecture ↗</Link></span></div>
  </>;
}
