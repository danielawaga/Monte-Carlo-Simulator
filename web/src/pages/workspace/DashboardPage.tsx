import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, BarChart3, ClipboardList, Play } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, CardTitle, PageHeader } from '../../components/common';
import { listRegisters, listRuns } from '../../services/savedProjects';
import { formatAmount, numeric, percentile } from '../../services/simulationMetrics';
import type { SavedRegister, SavedRun } from '../../types';

/**
 * Everything shown here comes from the registers and runs stored on this
 * machine. The page used to display a fabricated portfolio — invented owners,
 * exposures and review dates — which read exactly like a real result. In a tool
 * whose output is a figure sent to a client, that is the last place to keep
 * plausible fiction.
 */

function shortDate(iso: string) {
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime())
    ? iso
    : parsed.toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
}

function runAmount(run: SavedRun, label: string, key = 'amount') {
  return formatAmount(numeric(percentile(run.result, label), key), run.result.project.unit);
}

function runMean(run: SavedRun) {
  return formatAmount(numeric(run.result.summary, 'mean'), run.result.project.unit);
}

/** Bar widths are relative to the largest figure, so they compare honestly. */
function positions(run: SavedRun) {
  const unit = run.result.project.unit;
  const rows = [
    { label: 'Valeur de référence', value: run.result.project.baseline, tone: 'baseline' },
    { label: 'Coût moyen simulé', value: numeric(run.result.summary, 'mean'), tone: 'mean' },
    { label: 'P80', value: numeric(percentile(run.result, 'P80'), 'amount'), tone: 'p80' },
    { label: 'P90', value: numeric(percentile(run.result, 'P90'), 'amount'), tone: 'p90' },
  ].filter((row) => row.value !== null);
  const largest = Math.max(...rows.map((row) => Number(row.value)), 0);
  return rows.map((row) => ({
    label: row.label,
    tone: row.tone,
    text: formatAmount(Number(row.value), unit),
    width: largest > 0 ? Math.round((Number(row.value) / largest) * 100) : 0,
  }));
}

/** The engine's own sensitivity ranking — no aggregation invented here. */
function contributors(run: SavedRun) {
  const rows = [...run.result.sensitivity]
    .filter((row) => typeof row.spearman_rho === 'number')
    .sort((left, right) => Math.abs(Number(right.spearman_rho)) - Math.abs(Number(left.spearman_rho)))
    .slice(0, 4);
  const strongest = Math.abs(Number(rows[0]?.spearman_rho ?? 0));
  const tones = ['orange', 'blue', 'green', 'gray'];
  return rows.map((row, index) => ({
    name: String(row.item_name),
    rho: Number(row.spearman_rho),
    tone: tones[index] ?? 'gray',
    width: strongest > 0 ? Math.round((Math.abs(Number(row.spearman_rho)) / strongest) * 100) : 0,
  }));
}

function KpiTile({ label, value, detail, tone }: { label: string; value: string; detail: string; tone: string }) {
  return (
    <Card className="pro-kpi">
      <div className={`pro-kpi-accent ${tone}`} />
      <span>{label}</span><strong>{value}</strong><small>{detail}</small>
    </Card>
  );
}

function EmptyDashboard() {
  return (
    <Card className="dashboard-empty">
      <span className="dashboard-empty-icon"><ClipboardList /></span>
      <h2>Aucune donnée sur ce poste</h2>
      <p>
        Cet écran se remplit à partir des registres que vous enregistrez et des simulations
        que vous conservez. Rien n’est encore stocké dans la base locale.
      </p>
      <Link className="button primary" to="/risques">Préparer un registre de risques <ArrowRight /></Link>
    </Card>
  );
}

export function DashboardPage() {
  const [registers, setRegisters] = useState<SavedRegister[] | null>(null);
  const [runs, setRuns] = useState<SavedRun[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listRegisters(), listRuns()])
      .then(([savedRegisters, savedRuns]) => {
        if (cancelled) return;
        setRegisters(savedRegisters);
        setRuns(savedRuns);
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setRegisters([]);
          setError(cause instanceof Error ? cause.message : 'Les données locales sont illisibles.');
        }
      });
    return () => { cancelled = true; };
  }, []);

  const latest = runs[0];
  const header = (
    <PageHeader
      title="Tableau de bord"
      subtitle="Ce que contient la base locale de ce poste."
      actions={<Link className="button primary" to="/configuration"><Play />Lancer une simulation</Link>}
    />
  );

  if (registers === null) {
    return <>{header}<p className="dashboard-loading">Lecture de la base locale…</p></>;
  }

  if (error !== null) {
    return <>{header}<Card className="dashboard-empty"><span className="dashboard-empty-icon alert"><AlertTriangle /></span><h2>Base locale illisible</h2><p>{error}</p></Card></>;
  }

  if (registers.length === 0 && runs.length === 0) {
    return <>{header}<EmptyDashboard /></>;
  }

  return (
    <>
      {header}

      <div className="pro-context-bar">
        <div><span>Registres enregistrés</span><b>{registers.length}</b></div>
        <div><span>Simulations conservées</span><b>{runs.length}</b></div>
        <div><span>Dernière exécution</span><b>{latest ? shortDate(latest.createdAt) : 'Aucune'}</b></div>
        <div><span>Emplacement</span><b>Ce poste uniquement</b></div>
      </div>

      {latest ? (
        <div className="pro-kpi-grid">
          <KpiTile label="Coût moyen simulé" value={runMean(latest)} detail={latest.label} tone="blue" />
          <KpiTile label="P80" value={runAmount(latest, 'P80')} detail="Niveau de décision usuel" tone="orange" />
          <KpiTile label="P90" value={runAmount(latest, 'P90')} detail="Exposition haute" tone="red" />
          <KpiTile
            label="Réserve recommandée P80"
            value={runAmount(latest, 'P80', 'recommended_reserve')}
            detail="Écart positif à la référence"
            tone="navy"
          />
        </div>
      ) : null}

      <div className="pro-dashboard-grid">
        <Card className="pro-panel">
          <CardTitle info={false}>Positionnement budgétaire</CardTitle>
          <p className="pro-card-subtitle">
            {latest
              ? <>Dernière simulation conservée : <b>{latest.label}</b>, {shortDate(latest.createdAt)}.</>
              : 'Aucune simulation n’a encore été conservée.'}
          </p>
          {latest ? (
            <div className="budget-position">
              {positions(latest).map((row) => (
                <div className="budget-row" key={row.label}>
                  <div><span>{row.label}</span><b>{row.text}</b></div>
                  <div className="budget-track"><i className={row.tone} style={{ width: `${row.width}%` }} /></div>
                </div>
              ))}
            </div>
          ) : (
            <p className="panel-placeholder">Lancez une simulation, puis conservez-la depuis la page Résultats.</p>
          )}
        </Card>

        <Card className="pro-panel">
          <CardTitle info={false}>Postes les plus influents</CardTitle>
          <p className="pro-card-subtitle">Corrélation de Spearman calculée par le moteur sur la dernière exécution.</p>
          {latest && contributors(latest).length > 0 ? (
            <div className="exposure-list">
              {contributors(latest).map((row) => (
                <div key={row.name}>
                  <span>{row.name}</span>
                  <div><i className={row.tone} style={{ width: `${row.width}%` }} /></div>
                  <b>{row.rho.toLocaleString('fr-FR', { maximumFractionDigits: 2, signDisplay: 'always' })}</b>
                </div>
              ))}
            </div>
          ) : (
            <p className="panel-placeholder">Disponible dès qu’une simulation est conservée.</p>
          )}
          <Link className="pro-inline-link" to="/resultats">Ouvrir l’analyse complète <ArrowRight /></Link>
        </Card>
      </div>

      <div className="pro-dashboard-grid lower">
        <Card className="pro-panel pro-runs">
          <CardTitle info={false} action={<Link className="pro-inline-link" to="/resultats">Ouvrir l’analyse <ArrowRight /></Link>}>Dernières simulations</CardTitle>
          {runs.length > 0 ? (
            <div className="table-wrap">
              <table className="pro-table">
                <thead><tr><th>Exécution</th><th>Registre</th><th>Tirages</th><th>Moyenne</th><th>P80</th></tr></thead>
                <tbody>
                  {runs.slice(0, 5).map((run) => (
                    <tr key={run.id}>
                      <td><b>{run.label}</b><small>{shortDate(run.createdAt)}</small></td>
                      <td>{registers.find((item) => item.id === run.registerId)?.name ?? '—'}</td>
                      <td>{run.result.run.simulations.toLocaleString('fr-FR')}</td>
                      <td>{runMean(run)}</td>
                      <td>{runAmount(run, 'P80')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="panel-placeholder">Aucune simulation conservée pour l’instant.</p>
          )}
        </Card>

        <Card className="pro-panel">
          <CardTitle info={false} action={<Link className="pro-inline-link" to="/risques">Gérer <ArrowRight /></Link>}>Registres enregistrés</CardTitle>
          {registers.length > 0 ? (
            <ul className="register-list">
              {registers.slice(0, 5).map((register) => (
                <li key={register.id}>
                  <span className="register-icon"><BarChart3 /></span>
                  <div>
                    <b>{register.name}</b>
                    <small>{register.register.items.length} poste{register.register.items.length > 1 ? 's' : ''} · modifié le {shortDate(register.updatedAt)}</small>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="panel-placeholder">Aucun registre enregistré.</p>
          )}
        </Card>
      </div>
    </>
  );
}
