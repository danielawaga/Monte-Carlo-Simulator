import { FileSpreadsheet, FolderOpen, Play, RefreshCw, Save, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, CardTitle, PageHeader, SelectButton, StatusPill } from '../components/common';
import { AssumptionsSection } from '../components/configuration/AssumptionsSection';
import { StatCard } from '../components/cards/StatCard';
import { RiskPreviewTable } from '../components/tables/RiskPreviewTable';

export function SimulationConfigurationPage() {
  const navigate = useNavigate();
  const [scenarioMenuOpen, setScenarioMenuOpen] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState('Référence validée · SIM-260816-03');
  const [loadedScenario, setLoadedScenario] = useState('');
  const [fileName, setFileName] = useState('Registre_Risques_Projet_Atlas.xlsx');
  const [seed, setSeed] = useState('20260816');
  const [configurationSaved, setConfigurationSaved] = useState(false);

  return (
    <>
      <PageHeader
        title="Configuration de la simulation"
        subtitle="Configurez les paramètres de la simulation de Monte Carlo et lancez l’analyse."
        actions={<SelectButton aria-expanded={scenarioMenuOpen} onClick={() => setScenarioMenuOpen((open) => !open)}><FolderOpen />Charger un scénario</SelectButton>}
      />
      {scenarioMenuOpen ? <Card className="scenario-loader"><label>Scénario enregistré<select value={selectedScenario} onChange={(event) => setSelectedScenario(event.target.value)}><option>Référence validée · SIM-260816-03</option><option>Plan de mitigation v2 · SIM-260816-02</option><option>Stress fournisseurs · SIM-260815-06</option></select></label><div><Button onClick={() => setScenarioMenuOpen(false)}>Annuler</Button><Button variant="primary" onClick={() => { setLoadedScenario(selectedScenario); setScenarioMenuOpen(false); }}>Charger la configuration</Button></div></Card> : null}
      {loadedScenario ? <div className="pro-success-banner"><Save />Configuration « {loadedScenario} » chargée.</div> : null}
      <div className="config-grid">
        <Card className="upload">
          <CardTitle info={false}>Registre de risques (Excel)</CardTitle>
          <p>Importer un fichier .xlsx depuis votre registre de risques.</p>
          <div className="dropzone"><FileSpreadsheet /><span>Glissez-déposez votre fichier Excel ici<br />ou</span><label className="button secondary">Parcourir les fichiers<input className="sr-only" type="file" accept=".xlsx,.xls" onChange={(event) => { const selectedFile = event.target.files?.[0]; if (selectedFile) setFileName(selectedFile.name); }} /></label></div>
          {fileName ? <div className="file-row"><FileSpreadsheet /><div><strong>{fileName}</strong><small>31,8 Ko • Importé le 16/08/2026 à 17:54</small></div><StatusPill>Fichier valide</StatusPill><Button aria-label="Retirer le registre importé" onClick={() => setFileName('')}><Trash2 /></Button></div> : <div className="config-empty-file">Aucun registre chargé. Importez un fichier Excel pour lancer une simulation.</div>}
        </Card>
        <div className="parameters">
          <Card><CardTitle>Nombre de simulations</CardTitle><input value="50 000" readOnly /><small>Standard approuvé pour le reporting de gouvernance</small></Card>
          <Card><CardTitle>Graine aléatoire (seed)</CardTitle><div className="input-action"><input value={seed} readOnly /><Button aria-label="Générer une nouvelle graine" onClick={() => setSeed(String(Math.floor(10000000 + Math.random() * 90000000)))}><RefreshCw /></Button></div><small>Conservée pour assurer la reproductibilité</small></Card>
        </div>
        <Card className="levels">
          <CardTitle>Niveaux de confiance</CardTitle>
          {[50, 80, 90, 95].map((level) => <label key={level}><b>P{level}</b><input value={level} readOnly /><span>%</span></label>)}
          <p>Les percentiles seront calculés sur la distribution des résultats.</p>
        </Card>
        <AssumptionsSection />
        <Card className="summary-strip">
          <StatCard label="Estimation de référence (coût)" value="2 450 000 €" sub="Définie dans le registre de risques" />
          <StatCard label="Risques suivis" value="10" sub="1 critique · 4 élevés" icon="alert" />
          <StatCard label="Horizon d’analyse" value="31/12/2026" sub="Fin de projet approuvée" icon="shield" />
        </Card>
        <RiskPreviewTable />
        {configurationSaved ? <div className="pro-success-banner config-save-confirmation"><Save />Configuration enregistrée avec la graine {seed}.</div> : null}
        <div className="page-actions"><Button onClick={() => setConfigurationSaved(true)}><Save />Enregistrer la configuration</Button><Button variant="primary" disabled={!fileName} onClick={() => navigate('/resultats')}><Play />Lancer la simulation</Button></div>
      </div>
    </>
  );
}
