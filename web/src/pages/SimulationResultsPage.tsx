import {
  Activity,
  Archive,
  BarChart3,
  CheckCircle2,
  Copy,
  Dices,
  Download,
  Gauge,
  Info,
  Link2,
  PackageOpen,
  Save,
  Target,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { StatCard } from '../components/cards/StatCard';
import { ConvergenceChartCard, LiveHistogramCard, LiveSCurveCard, TornadoChartCard } from '../components/charts/LiveCharts';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../components/common';
import { simulationService } from '../services/simulationService';
import { saveSharedRun } from '../services/sharedProjects';
import { formatAmount, numeric, percentile } from '../services/simulationMetrics';
import { useSimulation } from '../state/SimulationContext';
import type { NumericRecord, SimulationResponse } from '../types';

type ResultTab = 'summary' | 'distribution' | 'sensitivity' | 'robustness';
type DistributionView = 'histogram' | 'curve';

const sections = [
  { value: 'summary', label: 'Synthèse', icon: Target },
  { value: 'distribution', label: 'Distribution', icon: BarChart3 },
  { value: 'sensitivity', label: 'Sensibilité', icon: Activity },
  { value: 'robustness', label: 'Robustesse', icon: Gauge },
] as const;

function boolean(record: NumericRecord | undefined, key: string) {
  return record?.[key] === true || String(record?.[key]).toLowerCase() === 'true';
}

function probability(value: number | null) {
  return value === null ? 'Non disponible' : `${(value * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`;
}

function shortAmount(value: number | null, unit: string) {
  return value === null ? 'N/D' : `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} ${unit}`;
}

function resultSummary(result: SimulationResponse) {
  const baseline = result.baselineComparison[0];
  return {
    mean: formatAmount(numeric(result.summary, 'mean'), result.project.unit),
    p80: formatAmount(numeric(percentile(result, 'P80'), 'amount'), result.project.unit),
    p90: formatAmount(numeric(percentile(result, 'P90'), 'amount'), result.project.unit),
    exceedance: probability(numeric(baseline, 'exceedance_probability')),
    baseline: formatAmount(result.project.baseline, result.project.unit),
    reserve: formatAmount(numeric(percentile(result, 'P80'), 'recommended_reserve'), result.project.unit),
  };
}

function ReadingCard({ result }: { result: SimulationResponse }) {
  const values = [
    ['Moyenne', numeric(result.summary, 'mean')],
    ['Écart-type', numeric(result.summary, 'std')],
    ['Minimum observé', numeric(result.summary, 'minimum')],
    ['Maximum observé', numeric(result.summary, 'maximum')],
    ['P80', numeric(percentile(result, 'P80'), 'amount')],
    ['P90', numeric(percentile(result, 'P90'), 'amount')],
  ] as const;
  return <Card className="result-reading-card"><CardTitle info={false}>Fiche de lecture</CardTitle><dl>{values.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{shortAmount(value, result.project.unit)}</dd></div>)}</dl><p><Info />Survolez le graphique pour lire précisément une classe ou un point de probabilité.</p></Card>;
}

function SummarySection({ result, decisionPercentile }: { result: SimulationResponse; decisionPercentile: number }) {
  const summary = resultSummary(result);
  const decision = percentile(result, `P${decisionPercentile}`);
  return <>
    <div className="kpi-grid"><StatCard label="Moyenne" value={summary.mean} icon="money" /><StatCard label={`P${decisionPercentile} — niveau de décision`} value={formatAmount(numeric(decision, 'amount'), result.project.unit)} /><StatCard label="P90" value={summary.p90} /><StatCard label="Probabilité de dépassement" value={summary.exceedance} sub="Par rapport à la référence" icon="alert" /></div>
    <div className="result-summary-layout">
      <Card className="decision-landmarks-card"><CardTitle info={false}>Repères de décision</CardTitle><div className="decision-landmarks">
        {result.percentiles.map((row) => <div className={row.percentile === `P${decisionPercentile}` ? 'decision' : ''} key={String(row.percentile)}><span>{String(row.percentile)}</span><b>{shortAmount(numeric(row, 'amount'), result.project.unit)}</b><small>Réserve : {shortAmount(numeric(row, 'recommended_reserve'), result.project.unit)}</small></div>)}
      </div><p className="note">Le percentile de décision est mis en évidence. La réserve reste nulle lorsque la valeur simulée est inférieure à la référence.</p></Card>
      <div className="summary-side-stats"><StatCard label="Valeur de référence" value={summary.baseline} sub="Issue du registre" /><StatCard label="Réserve recommandée P80" value={summary.reserve} sub="Écart positif à la référence" icon="shield" /><StatCard label="Dispersion (écart-type)" value={formatAmount(numeric(result.summary, 'std'), result.project.unit)} sub={`${result.run.simulations.toLocaleString('fr-FR')} tirages analysés`} /></div>
    </div>
  </>;
}

function DistributionSection({ result }: { result: SimulationResponse }) {
  const [view, setView] = useState<DistributionView>('histogram');
  return <>
    <div className="result-view-switch" role="tablist" aria-label="Type de visualisation de la distribution">
      <button type="button" role="tab" aria-selected={view === 'histogram'} className={view === 'histogram' ? 'active' : ''} onClick={() => setView('histogram')}>Histogramme</button>
      <button type="button" role="tab" aria-selected={view === 'curve'} className={view === 'curve' ? 'active' : ''} onClick={() => setView('curve')}>S-curve</button>
    </div>
    <div className="result-analysis-layout">{view === 'histogram' ? <LiveHistogramCard result={result} /> : <LiveSCurveCard current={result} />}<ReadingCard result={result} /></div>
  </>;
}

function SensitivitySection({ result }: { result: SimulationResponse }) {
  const sensitivity = [...result.sensitivity].sort((left, right) => Math.abs(Number(right.spearman_rho ?? 0)) - Math.abs(Number(left.spearman_rho ?? 0))).slice(0, 8);
  return <div className="result-analysis-layout sensitivity-layout"><TornadoChartCard result={result} /><Card className="sensitivity-ranking-card"><CardTitle info={false}>Classement des postes</CardTitle><div className="sensitivity-ranking">{sensitivity.map((row, index) => <div key={`${String(row.item_name)}-${index}`}><i>{index + 1}</i><span><b>{String(row.item_name)}</b><small>{Number(row.spearman_rho) >= 0 ? 'Influence positive' : 'Influence négative'}</small></span><strong>{typeof row.spearman_rho === 'number' ? row.spearman_rho.toLocaleString('fr-FR', { maximumFractionDigits: 3, signDisplay: 'always' }) : 'N/D'}</strong></div>)}</div><p className="note">Plus la valeur absolue du coefficient est élevée, plus le poste influence le résultat total.</p></Card></div>;
}

function RobustnessSection({ result }: { result: SimulationResponse }) {
  const lastConvergence = result.convergence.at(-1);
  const diagnostic = result.correlationDiagnostics[0];
  const stable = boolean(lastConvergence, 'stop_recommended');
  return <div className="result-analysis-layout robustness-layout"><ConvergenceChartCard result={result} /><Card className="robustness-card"><CardTitle info={false}>Diagnostic du calcul</CardTitle><div className={`robustness-status ${stable ? 'stable' : 'watch'}`}><Gauge /><span><b>{stable ? 'Convergence stabilisée' : 'Convergence à surveiller'}</b><small>{lastConvergence ? `${Number(lastConvergence.draw_count).toLocaleString('fr-FR')} tirages au dernier contrôle` : 'Contrôle non disponible'}</small></span></div><dl>
    <div><dt>Percentile contrôlé</dt><dd>{String(lastConvergence?.target_percentile ?? 'N/D')}</dd></div>
    <div><dt>Variation relative</dt><dd>{probability(numeric(lastConvergence, 'relative_change'))}</dd></div>
    <div><dt>Corrélations</dt><dd>{result.run.correlationsEnabled ? 'Activées' : 'Indépendance'}</dd></div>
    {diagnostic ? <><div><dt>Valeur propre minimale</dt><dd>{numeric(diagnostic, 'minimum_eigenvalue')?.toLocaleString('fr-FR', { maximumFractionDigits: 4 }) ?? 'N/D'}</dd></div><div><dt>Conditionnement</dt><dd>{numeric(diagnostic, 'condition_number')?.toLocaleString('fr-FR', { maximumFractionDigits: 2 }) ?? 'N/D'}</dd></div><div><dt>Réparation automatique</dt><dd>{boolean(diagnostic, 'automatic_repair_applied') ? 'Oui' : 'Non'}</dd></div></> : null}
  </dl><p className="note">Le moteur analyse la stabilité sans corriger automatiquement les hypothèses ou la matrice fournie.</p></Card></div>;
}

export function SimulationResultsPage() {
  const { result, reference, register, projectSource, config, sharedRegisterId, freezeReference } = useSimulation();
  const [tab, setTab] = useState<ResultTab>('summary');
  const [shareState, setShareState] = useState<'idle' | 'copied' | 'error'>('idle');
  const [exportState, setExportState] = useState<'idle' | 'excel' | 'bundle' | 'error'>('idle');
  const [keepState, setKeepState] = useState<'idle' | 'saving' | 'kept' | 'error'>('idle');
  const [keepError, setKeepError] = useState('');

  const downloadResults = async (kind: 'excel' | 'bundle') => {
    if (!result || exportState === 'excel' || exportState === 'bundle') return;
    setExportState(kind);
    try {
      const blob = kind === 'excel'
        ? await simulationService.exportResults(result, register, config)
        : await simulationService.exportResultsBundle(result, register, config);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const projectSlug = result.project.name.trim().toLowerCase().replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'projet';
      link.href = url;
      link.download = kind === 'excel'
        ? `resultats-monte-carlo-${projectSlug}.xlsx`
        : `dossier-resultats-monte-carlo-${projectSlug}.zip`;
      link.click();
      URL.revokeObjectURL(url);
      setExportState('idle');
    } catch {
      setExportState('error');
    }
  };

  const copyPageAddress = async () => {
    try { await navigator.clipboard.writeText(window.location.href); setShareState('copied'); }
    catch { setShareState('error'); }
  };

  if (!result) return <>
    <PageHeader title="Résultats de la simulation" subtitle="Consultez les indicateurs et diagnostics d’une simulation calculée." />
    {keepError ? <div className="pro-error-banner register-banner" role="alert"><Info />{keepError}</div> : null}
    <Card className="results-empty-state"><Dices /><h2>Aucun résultat disponible</h2><p>{projectSource?'Configurez puis lancez une simulation pour afficher des résultats réels.':'Créez ou importez d’abord un registre de risques, puis configurez la simulation.'} Les données de démonstration ne remplacent plus silencieusement un calcul absent.</p><Link className="button primary" to={projectSource?'/configuration':'/risques'}>{projectSource?'Configurer une simulation':'Préparer un projet'}</Link></Card>
  </>;

  const keepRun = async () => {
    setKeepState('saving');
    setKeepError('');
    try {
      await saveSharedRun(
        config.scenarioName.trim() || result.project.name,
        config,
        result,
        sharedRegisterId ?? undefined,
      );
      setKeepState('kept');
    } catch (cause) {
      setKeepError(cause instanceof Error ? cause.message : 'L’enregistrement a échoué.');
      setKeepState('error');
    }
  };

  const referenceFrozen = reference?.run.generatedAt === result.run.generatedAt;
  return <>
    <PageHeader title="Résultats de la simulation" subtitle={`Analyse réelle du projet ${result.project.name}.`} actions={<><Button onClick={()=>void downloadResults('excel')} disabled={exportState === 'excel'||exportState === 'bundle'}><Download />{exportState === 'excel' ? 'Préparation…' : 'Exporter Excel'}</Button><Button onClick={()=>void downloadResults('bundle')} disabled={exportState === 'excel'||exportState === 'bundle'}><PackageOpen />{exportState === 'bundle' ? 'Création du ZIP…' : 'Télécharger le dossier ZIP'}</Button><Button onClick={()=>void keepRun()} disabled={keepState === 'saving'} title="Conserver cette exécution pour l’équipe, avec son auteur et ses hypothèses."><Archive />{keepState === 'saving' ? 'Enregistrement…' : keepState === 'kept' ? 'Exécution conservée' : 'Conserver pour l’équipe'}</Button><Button onClick={freezeReference}><Save />{referenceFrozen ? 'Référence enregistrée' : 'Geler comme référence'}</Button>{reference ? <Link className="button secondary" to="/comparaison"><Copy />Comparer</Link> : null}<Button onClick={()=>void copyPageAddress()}>{shareState === 'copied' ? <CheckCircle2 /> : <Link2 />}{shareState === 'copied' ? 'Adresse copiée' : shareState === 'error' ? 'Copie impossible' : 'Copier l’adresse'}</Button></>} />
    {exportState === 'error' ? <div className="pro-error-banner results-action-message" role="alert">Le fichier demandé n’a pas pu être généré. Vérifiez que l’API est démarrée puis réessayez.</div> : null}
    {shareState === 'copied' ? <div className="results-action-message results-action-message--info" role="status">L’adresse de cette page est copiée. Pour transmettre les données de la simulation, partagez plutôt le fichier Excel exporté.</div> : null}
    <div className="result-governance-bar"><div><span>Projet</span><b>{result.project.name}</b></div><div><span>Exécution</span><b>{new Date(result.run.generatedAt).toLocaleString('fr-FR')}</b></div><div><span>Tirages</span><b>{result.run.simulations.toLocaleString('fr-FR')}</b></div><div><span>Graine</span><b>{result.run.seed}</b></div><div><span>Corrélations</span><b>{result.run.correlationsEnabled ? 'Actives' : 'Indépendance'}</b></div><div><span>Source</span><StatusPill>Moteur Python</StatusPill></div></div>
    <div className="result-workflow" role="tablist" aria-label="Analyse des résultats">{sections.map(({ value, label, icon: Icon }) => <button type="button" role="tab" aria-selected={tab === value} className={tab === value ? 'active' : ''} onClick={() => setTab(value)} key={value}><Icon /><span>{label}</span></button>)}</div>
    <section className="result-section" aria-live="polite">
      {tab === 'summary' ? <SummarySection result={result} decisionPercentile={config.decisionPercentile} /> : null}
      {tab === 'distribution' ? <DistributionSection result={result} /> : null}
      {tab === 'sensitivity' ? <SensitivitySection result={result} /> : null}
      {tab === 'robustness' ? <RobustnessSection result={result} /> : null}
    </section>
    <div className="helpbar"><span><Info />Résultats reproductibles avec la graine {result.run.seed}.</span><span><Link to="/aide">Consulter la méthode et les règles de lecture ↗</Link></span></div>
  </>;
}
