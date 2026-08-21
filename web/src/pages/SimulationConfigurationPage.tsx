import { AlertTriangle, ArrowRight, CheckCircle2, ClipboardList, Copy, Dices, Edit3, Play, RefreshCw, Save, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../components/common';
import { simulationService } from '../services/simulationService';
import { useSimulation } from '../state/SimulationContext';
import type { SimulationWorkspaceConfig } from '../types';

const numberOrNull=(value:string)=>value===''?null:Number(value);

export function SimulationConfigurationPage(){
  const navigate=useNavigate();
  const [searchParams,setSearchParams]=useSearchParams();
  const {register,projectSource,config,setConfig,setResult,scenarios,saveScenario,loadScenario,deleteScenario}=useSimulation();
  const tab=searchParams.get('tab')==='scenarios'?'scenarios':'configuration';
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const [running,setRunning]=useState(false);
  const activeItems=useMemo(()=>register.items.filter((item)=>item.enabled),[register.items]);
  const update=(patch:Partial<SimulationWorkspaceConfig>)=>{setConfig({...config,...patch});setMessage('');setError('')};
  const setTab=(value:'configuration'|'scenarios')=>setSearchParams(value==='scenarios'?{tab:'scenarios'}:{});
  const toggleLevel=(level:number)=>{
    const levels=config.levels.includes(level)?config.levels.filter((item)=>item!==level):[...config.levels,level].sort((a,b)=>a-b);
    if(levels.length)update({levels});
  };
  const run=async()=>{
    setRunning(true);setError('');setMessage('');
    try{const result=await simulationService.simulateDraft(register,config);setResult(result);navigate('/resultats')}
    catch(reason){setError(reason instanceof Error?reason.message:'La simulation a échoué.')}
    finally{setRunning(false)}
  };
  const save=()=>{const saved=saveScenario();setMessage(`Le scénario « ${saved.name} » a été enregistré.`)};
  const load=(id:string)=>{loadScenario(id);setMessage('Le scénario et son registre ont été chargés.');setTab('configuration')};
  const projectReady=Boolean(projectSource&&register.metadata.projectName.trim()&&register.metadata.defaultUnit.trim()&&activeItems.length);

  if(!projectReady)return <>
    <PageHeader title="Simulation" subtitle="Réglez l’exécution, documentez le scénario et lancez l’analyse à partir d’un registre validé." />
    <Card className="simulation-blocker-card"><AlertTriangle/><div><h2>{!projectSource?'Commencez par créer ou importer un projet':'Le registre doit encore être complété'}</h2><p>{!projectSource?'La simulation utilise les informations du projet, ses postes et leurs éventuelles corrélations.':'Renseignez le nom, l’unité et au moins un poste actif avant de revenir à la configuration.'}</p><Button variant="primary" onClick={()=>navigate('/risques')}>{!projectSource?'Ouvrir le registre de risques':'Compléter le registre'}<ArrowRight/></Button></div></Card>
  </>;

  return <>
    <PageHeader title="Simulation" subtitle="Réglez l’exécution, documentez le scénario et lancez l’analyse à partir du registre courant." />
    <div className="simulation-tabs" role="tablist" aria-label="Simulation et scénarios"><button role="tab" aria-selected={tab==='configuration'} className={tab==='configuration'?'active':''} onClick={()=>setTab('configuration')}><Dices/>Configuration</button><button role="tab" aria-selected={tab==='scenarios'} className={tab==='scenarios'?'active':''} onClick={()=>setTab('scenarios')}><Copy/>Scénarios <span>{scenarios.length}</span></button></div>
    {message?<div className="pro-success-banner"><CheckCircle2/>{message}</div>:null}
    {error?<div className="pro-error-banner simulation-banner" role="alert">{error}</div>:null}

    {tab==='configuration'?<div className="simulation-workspace">
      <Card className="project-overview-card"><CardTitle info={false} action={<Button onClick={()=>navigate('/risques')}><Edit3/>Corriger le registre</Button>}>Aperçu du projet</CardTitle><div className="project-overview-grid"><div><span>Projet</span><b>{register.metadata.projectName||'Projet sans nom'}</b><small>{register.metadata.analysisType==='cost'?'Analyse de coût':'Analyse de durée'} · {register.metadata.defaultUnit}</small></div><div><span>Référence</span><b>{register.metadata.baselineEstimate?.toLocaleString('fr-FR')??'Non définie'} {register.metadata.baselineEstimate!==null?register.metadata.defaultUnit:''}</b><small>Valeur de comparaison, non ajoutée au total</small></div><div><span>Postes actifs</span><b>{activeItems.length}</b><small>{register.correlations.mode==='correlated'?'Matrice de corrélation':'Hypothèse d’indépendance'}</small></div><div><span>Schéma</span><b>Version {register.schemaVersion}</b><small>Compatible avec le moteur Python</small></div></div><div className="project-risk-preview"><table><thead><tr><th>Poste</th><th>Distribution</th><th>Catégorie</th><th>Unité</th></tr></thead><tbody>{activeItems.slice(0,5).map((item)=><tr key={item.id}><td><b>{item.name}</b></td><td>{item.distribution}</td><td>{item.category||'—'}</td><td>{item.unit||register.metadata.defaultUnit}</td></tr>)}</tbody></table>{activeItems.length>5?<div className="compact-table-note">+ {activeItems.length-5} autre(s) poste(s) dans le registre</div>:null}</div></Card>

      <div className="simulation-config-grid">
        <Card className="simulation-parameters-card"><CardTitle info={false}>Paramètres d’exécution</CardTitle><div className="simulation-form-grid"><label>Nombre de simulations<select value={config.simulations} onChange={(event)=>update({simulations:Number(event.target.value)})}><option value="10000">10 000</option><option value="50000">50 000</option><option value="100000">100 000</option><option value="250000">250 000</option></select><small>Plus le nombre est élevé, plus les estimations se stabilisent.</small></label><label>Graine aléatoire<div className="input-action"><input type="number" min="0" value={config.seed} onChange={(event)=>update({seed:Math.max(0,Number(event.target.value))})}/><Button aria-label="Générer une nouvelle graine" onClick={()=>update({seed:Math.floor(Math.random()*2_147_483_647)})}><RefreshCw/></Button></div><small>Même registre + mêmes réglages + même graine = mêmes tirages.</small></label><label>Méthode d’échantillonnage<select value={config.samplingMethod} disabled><option value="pseudo-random">Pseudo-aléatoire</option></select><small>Latin Hypercube sera proposé après validation dans le moteur.</small></label><label>Seuil de convergence<select value={config.convergenceTolerance} onChange={(event)=>update({convergenceTolerance:Number(event.target.value)})}><option value="0.5">0,5 %</option><option value="1">1 %</option><option value="2">2 %</option></select><small>Critère documenté pour l’analyse de stabilité.</small></label></div></Card>
        <Card className="decision-settings-card"><CardTitle info={false}>Niveaux et décision</CardTitle><div className="confidence-selector">{[50,75,80,90,95].map((level)=><label className={config.levels.includes(level)?'selected':''} key={level}><input type="checkbox" checked={config.levels.includes(level)} onChange={()=>toggleLevel(level)}/><b>P{level}</b></label>)}</div><div className="decision-form"><label>Niveau de décision<select value={config.decisionPercentile} onChange={(event)=>update({decisionPercentile:Number(event.target.value)})}>{config.levels.map((level)=><option value={level} key={level}>P{level}</option>)}</select></label><label>Seuil de dépassement ({register.metadata.defaultUnit})<input type="number" value={config.exceedanceThreshold??''} onChange={(event)=>update({exceedanceThreshold:numberOrNull(event.target.value)})}/></label></div><p>Les percentiles sélectionnés apparaîtront dans les résultats. Le niveau de décision sert de repère de gouvernance.</p></Card>
      </div>

      <Card className="scenario-definition-card"><CardTitle info={false} action={<Button onClick={save}><Save/>Enregistrer le scénario</Button>}>Documentation du scénario</CardTitle><div className="scenario-definition-form"><label>Nom du scénario<input value={config.scenarioName} onChange={(event)=>update({scenarioName:event.target.value})} placeholder="Ex. Référence, mitigation, stress…"/></label><label>Description et hypothèses<textarea value={config.scenarioDescription} onChange={(event)=>update({scenarioDescription:event.target.value})} placeholder="Mesures appliquées, sources et justification…"/></label></div></Card>

      <div className="simulation-preflight"><div><CheckCircle2/><span><b>Prêt à simuler</b><small>{activeItems.length} postes · {config.simulations.toLocaleString('fr-FR')} tirages · graine {config.seed}</small></span></div><div><Button onClick={save}><Save/>Enregistrer</Button><Button variant="primary" disabled={!activeItems.length||running||!config.levels.length} onClick={()=>void run()}><Play/>{running?'Calcul en cours…':'Lancer la simulation'}</Button></div></div>
    </div>:null}

    {tab==='scenarios'?<Card className="saved-scenarios-card"><CardTitle info={false} action={<Button onClick={()=>setTab('configuration')}><PlusIcon/>Nouveau scénario</Button>}>Scénarios enregistrés</CardTitle><p className="builder-intro">Chaque scénario conserve une copie du registre et des paramètres d’exécution afin de rendre les comparaisons reproductibles.</p>{scenarios.length?<div className="saved-scenario-list">{scenarios.map((scenario)=><article key={scenario.id}><span className="scenario-dot"/><div><b>{scenario.name}</b><p>{scenario.description||'Aucune description.'}</p><small>{new Date(scenario.savedAt).toLocaleString('fr-FR')} · {scenario.config.simulations.toLocaleString('fr-FR')} tirages · graine {scenario.config.seed}</small></div><StatusPill tone="blue">{scenario.register.items.filter((item)=>item.enabled).length} postes</StatusPill><Button onClick={()=>load(scenario.id)}>Charger</Button><Button aria-label={`Supprimer ${scenario.name}`} onClick={()=>deleteScenario(scenario.id)}><Trash2/></Button></article>)}</div>:<div className="pro-empty-state"><ClipboardList/><b>Aucun scénario enregistré</b><span>Documentez la configuration actuelle puis enregistrez-la pour la réutiliser.</span><Button variant="primary" onClick={()=>setTab('configuration')}>Configurer le premier scénario</Button></div>}</Card>:null}
  </>;
}

function PlusIcon(){return <span aria-hidden="true" className="button-plus">+</span>}
