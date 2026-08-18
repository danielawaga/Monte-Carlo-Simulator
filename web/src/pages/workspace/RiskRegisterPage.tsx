import { useState, type FormEvent } from 'react';
import { Download, Filter, Plus, Search, X } from 'lucide-react';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { portfolioRisks, type PortfolioRisk, type RiskLevel } from '../../data/workspaceData';

const formatCurrency = (amount: number) => `${amount.toLocaleString('fr-FR')} €`;
const categories = [...new Set(portfolioRisks.map(({ category }) => category))];

function levelTone(level: RiskLevel) {
  if (level === 'Critique') return 'red' as const;
  if (level === 'Élevé') return 'orange' as const;
  if (level === 'Modéré') return 'blue' as const;
  return 'gray' as const;
}

export function RiskRegisterPage() {
  const [riskRows, setRiskRows] = useState(portfolioRisks);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('Toutes');
  const [level, setLevel] = useState('Tous');
  const [showEditor, setShowEditor] = useState(false);

  const filteredRisks = riskRows.filter((risk) => {
    const matchesQuery = `${risk.id} ${risk.title} ${risk.owner}`.toLocaleLowerCase('fr').includes(query.toLocaleLowerCase('fr'));
    return matchesQuery && (category === 'Toutes' || risk.category === category) && (level === 'Tous' || risk.level === level);
  });

  const addRisk = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const probability = Number(form.get('probability'));
    const impact = Number(form.get('impact'));
    const levelValue = String(form.get('level')) as RiskLevel;
    const nextNumber = Math.max(...riskRows.map(({ id }) => Number(id.replace('R-', '')))) + 1;
    const newRisk: PortfolioRisk = {
      id: `R-${String(nextNumber).padStart(3, '0')}`,
      category: String(form.get('category')),
      title: String(form.get('title')),
      owner: String(form.get('owner')),
      probability,
      impact,
      exposure: Math.round(probability / 100 * impact),
      level: levelValue,
      status: 'Ouvert',
      treatment: 'Plan de réponse à définir',
      nextReview: '31/08/2026',
    };
    setRiskRows((current) => [newRisk, ...current]);
    setShowEditor(false);
  };

  const exportRegister = () => {
    const header = ['ID', 'Catégorie', 'Risque', 'Responsable', 'Probabilité', 'Impact', 'Exposition', 'Niveau', 'Statut'];
    const rows = filteredRisks.map((risk) => [risk.id, risk.category, risk.title, risk.owner, `${risk.probability}%`, risk.impact, risk.exposure, risk.level, risk.status]);
    const csv = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(';')).join('\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'registre-risques-atlas.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <PageHeader
        title="Registre de risques"
        subtitle="Référentiel de gouvernance — 10 risques suivis, exposition brute de 468,5 k€."
        actions={<><Button onClick={exportRegister}><Download />Exporter le registre</Button><Button variant="primary" onClick={() => setShowEditor(true)}><Plus />Nouveau risque</Button></>}
      />

      {showEditor ? (
        <Card className="pro-editor-card">
          <CardTitle info={false} action={<Button aria-label="Fermer le formulaire" onClick={() => setShowEditor(false)}><X /></Button>}>Créer une fiche de risque</CardTitle>
          <form className="risk-create-form" onSubmit={addRisk}>
            <label className="wide">Intitulé du risque<input name="title" required placeholder="Décrire l’événement redouté" /></label>
            <label>Catégorie<select name="category" defaultValue="Technique">{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Responsable<input name="owner" required placeholder="Nom du risk owner" /></label>
            <label>Probabilité (%)<input name="probability" type="number" min="1" max="100" required defaultValue="25" /></label>
            <label>Impact maximal (€)<input name="impact" type="number" min="0" step="1000" required defaultValue="100000" /></label>
            <label>Niveau<select name="level" defaultValue="Modéré"><option>Critique</option><option>Élevé</option><option>Modéré</option><option>Faible</option></select></label>
            <div className="risk-form-actions"><Button type="button" onClick={() => setShowEditor(false)}>Annuler</Button><Button variant="primary" type="submit">Créer la fiche</Button></div>
          </form>
        </Card>
      ) : null}

      <Card className="pro-register-card">
        <div className="register-toolbar">
          <label className="search-field"><Search /><span className="sr-only">Rechercher</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher par risque, ID ou responsable…" /></label>
          <div className="filter-group"><Filter /><select aria-label="Filtrer par catégorie" value={category} onChange={(event) => setCategory(event.target.value)}><option>Toutes</option>{categories.map((item) => <option key={item}>{item}</option>)}</select><select aria-label="Filtrer par niveau" value={level} onChange={(event) => setLevel(event.target.value)}><option>Tous</option><option>Critique</option><option>Élevé</option><option>Modéré</option><option>Faible</option></select></div>
        </div>
        <div className="register-summary"><span><b>{filteredRisks.length}</b> risque{filteredRisks.length > 1 ? 's' : ''} affiché{filteredRisks.length > 1 ? 's' : ''}</span><span>Dernière synchronisation : 17/08/2026 · 20:15</span></div>
        <div className="table-wrap">
          <table className="pro-table risk-register-table">
            <thead><tr><th>ID / risque</th><th>Responsable</th><th>Prob.</th><th>Impact max.</th><th>Exposition</th><th>Niveau</th><th>Plan de réponse</th><th>Revue</th></tr></thead>
            <tbody>{filteredRisks.map((risk) => <tr key={risk.id}><td><b>{risk.id}</b><strong>{risk.title}</strong><small>{risk.category} · {risk.status}</small></td><td>{risk.owner}</td><td>{risk.probability} %</td><td>{formatCurrency(risk.impact)}</td><td><b>{formatCurrency(risk.exposure)}</b></td><td><StatusPill tone={levelTone(risk.level)}>{risk.level}</StatusPill></td><td>{risk.treatment}</td><td>{risk.nextReview}</td></tr>)}</tbody>
          </table>
        </div>
        {filteredRisks.length === 0 ? <div className="pro-empty-state"><Search /><b>Aucun risque ne correspond aux filtres</b><span>Modifiez la recherche ou réinitialisez les critères.</span><Button onClick={() => { setQuery(''); setCategory('Toutes'); setLevel('Tous'); }}>Réinitialiser</Button></div> : null}
      </Card>
    </>
  );
}
