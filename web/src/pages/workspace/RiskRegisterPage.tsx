import { useMemo, useRef, useState } from 'react';
import { ArrowRight, CheckCircle2, Copy, Download, FilePlus2, Grid3X3, Info, Plus, Trash2, Upload, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { simulationService } from '../../services/simulationService';
import { useSimulation } from '../../state/SimulationContext';
import type { DistributionName, RegisterValidation, RiskDraft, RiskRegisterDraft } from '../../types';

type RegisterTab='project'|'items'|'correlations'|'validation';
const distributions:{value:DistributionName;label:string}[]=[
  {value:'triangular',label:'Triangulaire'},{value:'pert',label:'PERT'},{value:'uniform',label:'Uniforme'},
  {value:'normal',label:'Normale'},{value:'lognormal',label:'Lognormale'},{value:'event',label:'Événement'},
];

function blankRisk(index:number,unit:string):RiskDraft{
  return {id:`risk-${Date.now()}-${index}`,name:'',distribution:'triangular',minimum:null,mostLikely:null,maximum:null,mean:null,standardDeviation:null,probability:null,impact:null,lambdaShape:null,category:'',unit,enabled:true,notes:''};
}

function numberValue(value:string){return value===''?null:Number(value)}

function rowIssue(item:RiskDraft):string|null{
  if(!item.name.trim())return 'Le nom du poste est requis.';
  if(item.distribution==='triangular'||item.distribution==='pert'){
    if(item.minimum===null||item.mostLikely===null||item.maximum===null)return 'Min., probable et max. sont requis.';
    if(!(item.minimum<=item.mostLikely&&item.mostLikely<=item.maximum))return 'Respecter min. ≤ probable ≤ max.';
    if(item.distribution==='pert'&&item.lambdaShape!==null&&item.lambdaShape<=0)return 'Lambda doit être positif.';
  }
  if(item.distribution==='uniform'&&(item.minimum===null||item.maximum===null||item.minimum>item.maximum))return 'Renseigner min. ≤ max.';
  if((item.distribution==='normal'||item.distribution==='lognormal')&&(item.mean===null||item.standardDeviation===null||item.standardDeviation<0))return 'Moyenne et écart-type positif requis.';
  if(item.distribution==='lognormal'&&(item.mean??0)<=0)return 'La moyenne doit être positive.';
  if(item.distribution==='event'&&(item.probability===null||item.impact===null||item.probability<0||item.probability>1))return 'Probabilité [0 ; 1] et impact requis.';
  return null;
}

function activeNames(items:RiskDraft[]){return items.filter((item)=>item.enabled).map((item)=>item.name.trim())}

function reconcileCorrelations(register:RiskRegisterDraft,items:RiskDraft[]):RiskRegisterDraft['correlations']{
  if(register.correlations.mode==='independent')return register.correlations;
  const names=activeNames(items);
  const oldIndex=new Map(register.correlations.names.map((name,index)=>[name,index]));
  const values=names.map((rowName,row)=>names.map((columnName,column)=>{
    if(row===column)return 1;
    const oldRow=oldIndex.get(rowName);const oldColumn=oldIndex.get(columnName);
    return oldRow===undefined||oldColumn===undefined?0:register.correlations.values[oldRow]?.[oldColumn]??0;
  }));
  return {mode:'correlated',names,values};
}

function ParameterFields({item,onChange}:{item:RiskDraft;onChange:(patch:Partial<RiskDraft>)=>void}){
  const field=(label:string,key:keyof RiskDraft,value:number|null,extra:Record<string,string|number>={})=><label>{label}<input type="number" value={value??''} onChange={(event)=>onChange({[key]:numberValue(event.target.value)})} {...extra}/></label>;
  if(item.distribution==='triangular'||item.distribution==='pert')return <div className="risk-parameter-grid">{field('Minimum','minimum',item.minimum)}{field('Plus probable','mostLikely',item.mostLikely)}{field('Maximum','maximum',item.maximum)}{item.distribution==='pert'?field('Lambda','lambdaShape',item.lambdaShape??4,{min:.01,step:.1}):null}</div>;
  if(item.distribution==='uniform')return <div className="risk-parameter-grid">{field('Minimum','minimum',item.minimum)}{field('Maximum','maximum',item.maximum)}</div>;
  if(item.distribution==='normal'||item.distribution==='lognormal')return <div className="risk-parameter-grid">{field('Moyenne','mean',item.mean)}{field('Écart-type','standardDeviation',item.standardDeviation,{min:0})}</div>;
  return <div className="risk-parameter-grid">{field('Probabilité (0–1)','probability',item.probability,{min:0,max:1,step:.01})}{field('Impact','impact',item.impact)}</div>;
}

function WorkflowGuidance({title,detail,action,onAction}:{title:string;detail:string;action:string;onAction:()=>void}){
  return <div className="workflow-guidance" role="status"><Info/><div><b>{title}</b><span>{detail}</span></div><Button onClick={onAction}>{action}<ArrowRight/></Button></div>;
}

export function RiskRegisterPage(){
  const navigate=useNavigate();
  const fileInput=useRef<HTMLInputElement>(null);
  const {register,projectSource,setRegister,startNewProject,importProject}=useSimulation();
  const [tab,setTab]=useState<RegisterTab>('project');
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const [validation,setValidation]=useState<RegisterValidation|null>(null);
  const activeItems=useMemo(()=>register.items.filter((item)=>item.enabled),[register.items]);
  const localIssues=useMemo(()=>activeItems.map(rowIssue).filter(Boolean),[activeItems]);
  const projectReady=Boolean(projectSource&&register.metadata.projectName.trim()&&register.metadata.defaultUnit.trim());
  const correlationsReady=register.correlations.mode==='independent'||(register.correlations.names.length===activeItems.length&&register.correlations.values.length===activeItems.length);
  const canValidate=projectReady&&activeItems.length>0&&localIssues.length===0&&correlationsReady;

  const changeRegister=(next:RiskRegisterDraft)=>{setRegister(next);setValidation(null);setMessage('');setError('')};
  const changeItems=(items:RiskDraft[])=>changeRegister({...register,items,correlations:reconcileCorrelations(register,items)});
  const patchItem=(id:string,patch:Partial<RiskDraft>)=>changeItems(register.items.map((item)=>item.id===id?{...item,...patch}:item));
  const addItem=()=>{const next=blankRisk(register.items.length+1,register.metadata.defaultUnit);changeItems([...register.items,next]);setTab('items')};
  const duplicateItem=(item:RiskDraft)=>changeItems([...register.items,{...item,id:`risk-${Date.now()}`,name:`${item.name} — copie`}]);
  const removeItem=(id:string)=>changeItems(register.items.filter((item)=>item.id!==id));
  const createProject=()=>{startNewProject();setValidation(null);setMessage('Nouveau projet créé. Les exemples en filigrane vous indiquent le format attendu.');setError('');setTab('project')};

  const validate=async()=>{
    setBusy(true);setError('');setMessage('');
    try{const result=await simulationService.validateRegister(register);setValidation(result);setMessage('Registre validé par le moteur Monte-Carlo.');setTab('validation')}
    catch(reason){setValidation(null);setError(reason instanceof Error?reason.message:'La validation a échoué.');setTab('validation')}
    finally{setBusy(false)}
  };
  const exportExcel=async()=>{
    setBusy(true);setError('');
    try{const blob=await simulationService.exportRegister(register);const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`registre-${register.metadata.projectName.trim().toLowerCase().replace(/[^a-z0-9]+/gi,'-')||'projet'}.xlsx`;link.click();URL.revokeObjectURL(url);setMessage('Registre Excel compatible téléchargé.')}
    catch(reason){setError(reason instanceof Error?reason.message:'L’export a échoué.')}
    finally{setBusy(false)}
  };
  const importExcel=async(file:File|null)=>{
    if(!file)return;setBusy(true);setError('');
    try{const imported=await simulationService.importRegister(file);importProject(imported);setValidation(null);setMessage(`Le registre « ${file.name} » a été contrôlé à l’import. Vérifiez les corrélations puis lancez la validation finale.`);setTab('project')}
    catch(reason){setError(reason instanceof Error?reason.message:'L’import a échoué.')}
    finally{setBusy(false);if(fileInput.current)fileInput.current.value=''}
  };
  const setCorrelationMode=(mode:'independent'|'correlated')=>{
    const names=activeNames(register.items);
    const values=names.map((_name,row)=>names.map((_other,column)=>row===column?1:0));
    changeRegister({...register,correlations:mode==='independent'?{mode,names:[],values:[]}:{mode,names,values}});
  };
  const changeCoefficient=(row:number,column:number,value:number)=>{
    const values=register.correlations.values.map((line)=>[...line]);
    values[row][column]=value;values[column][row]=value;
    changeRegister({...register,correlations:{...register.correlations,values}});
  };

  return <>
    <PageHeader title="Registre de risques" subtitle="Préparez le projet, ses postes probabilistes et leurs dépendances dans un registre compatible avec le moteur." actions={<><input ref={fileInput} className="sr-only" type="file" accept=".xlsx" onChange={(event)=>void importExcel(event.target.files?.[0]??null)}/><Button onClick={()=>fileInput.current?.click()} disabled={busy}><Upload/>Importer Excel</Button><Button onClick={()=>void exportExcel()} disabled={busy||!canValidate} title={!canValidate?'Complétez le projet, les postes et les corrélations avant le téléchargement.':undefined}><Download/>Télécharger Excel</Button></>}/>
    <div className="register-workflow" role="tablist" aria-label="Construction du registre">
      {([['project','1','Projet'],['items','2','Postes'],['correlations','3','Corrélations'],['validation','4','Validation']] as const).map(([value,index,label])=><button key={value} role="tab" aria-selected={tab===value} className={tab===value?'active':''} onClick={()=>setTab(value)}><i>{index}</i><span>{label}</span>{value==='items'?<small>{activeItems.length} actif{activeItems.length>1?'s':''}</small>:null}</button>)}
    </div>
    {message?<div className="pro-success-banner"><CheckCircle2/>{message}</div>:null}
    {error?<div className="pro-error-banner register-banner" role="alert"><XCircle/>{error}</div>:null}

    {tab==='project'&&!projectSource?<Card className="project-entry-card"><div className="project-entry-intro"><FilePlus2/><div><h2>Commencer un registre de risques</h2><p>Choisissez comment initialiser le projet. Le formulaire d’identité apparaîtra seulement après cette étape.</p></div></div><div className="project-entry-options"><button type="button" onClick={createProject}><FilePlus2/><span><b>Créer un nouveau projet</b><small>Partez d’un formulaire vide avec des exemples en filigrane.</small></span><ArrowRight/></button><button type="button" onClick={()=>fileInput.current?.click()} disabled={busy}><Upload/><span><b>Importer un registre Excel</b><small>Les informations du projet et les postes seront préremplis.</small></span><ArrowRight/></button></div></Card>:null}

    {tab==='project'&&projectSource?<Card className="register-builder-card"><CardTitle info={false} action={<div className="project-card-actions"><StatusPill tone={projectSource==='imported'?'blue':'orange'}>{projectSource==='imported'?'Projet importé':'Nouveau projet'}</StatusPill><Button onClick={createProject}><FilePlus2/>Créer un autre projet</Button></div>}>Identité et cadre de l’analyse</CardTitle><div className="pro-form-grid register-project-form">
      <label className="wide">Nom du projet<input value={register.metadata.projectName} onChange={(event)=>changeRegister({...register,metadata:{...register.metadata,projectName:event.target.value}})} placeholder="Ex. Extension de l’usine de Casablanca"/></label>
      <label>Type de risque étudié<select value={register.metadata.analysisType} onChange={(event)=>changeRegister({...register,metadata:{...register.metadata,analysisType:event.target.value as 'cost'|'duration'}})}><option value="cost">Coût</option><option value="duration">Durée</option></select></label>
      <label>Unité commune<input value={register.metadata.defaultUnit} onChange={(event)=>changeRegister({...register,metadata:{...register.metadata,defaultUnit:event.target.value}})} placeholder="Ex. MAD, EUR ou jours"/></label>
      <label>Estimation de référence<input type="number" value={register.metadata.baselineEstimate??''} onChange={(event)=>changeRegister({...register,metadata:{...register.metadata,baselineEstimate:numberValue(event.target.value)}})} placeholder="Ex. 2500000"/></label>
      <label className="wide">Description<textarea value={register.metadata.description} onChange={(event)=>changeRegister({...register,metadata:{...register.metadata,description:event.target.value}})} placeholder="Ex. Analyse des incertitudes du budget prévisionnel avant validation du marché."/></label>
    </div>{!projectReady?<WorkflowGuidance title="Deux renseignements sont encore nécessaires" detail="Renseignez au minimum le nom du projet et son unité commune avant de définir les postes." action="Compléter le projet" onAction={()=>setTab('project')}/>:null}<div className="builder-footer"><span>Le brouillon est enregistré automatiquement dans ce navigateur.</span><Button variant="primary" disabled={!projectReady} onClick={()=>setTab('items')}>Continuer vers les postes</Button></div></Card>:null}

    {tab==='items'?<Card className="register-builder-card risk-items-card"><CardTitle info={false} action={<Button onClick={addItem} disabled={!projectReady}><Plus/>Ajouter un poste</Button>}>Postes et distributions</CardTitle>{!projectReady?<WorkflowGuidance title="Projet incomplet" detail="Créez ou importez un projet, puis renseignez son nom et son unité avant d’ajouter des postes." action="Revenir au projet" onAction={()=>setTab('project')}/>:null}<p className="builder-intro">Chaque ligne représente une composante incertaine du coût ou de la durée. Les paramètres affichés s’adaptent à la distribution choisie.</p>{projectReady&&!register.items.length?<div className="register-empty-step"><Plus/><b>Aucun poste pour le moment</b><span>Ajoutez le premier poste incertain du projet pour choisir sa distribution.</span><Button variant="primary" onClick={addItem}>Ajouter le premier poste</Button></div>:null}<div className="risk-editor-list">
      {register.items.map((item,index)=>{const issue=item.enabled?rowIssue(item):null;return <article className={`risk-editor-row ${!item.enabled?'disabled':''}`} key={item.id}>
        <div className="risk-row-heading"><span>{String(index+1).padStart(2,'0')}</span><label>Nom du poste<input value={item.name} onChange={(event)=>patchItem(item.id,{name:event.target.value})} placeholder="Ex. Études détaillées"/></label><label>Distribution<select value={item.distribution} onChange={(event)=>patchItem(item.id,{distribution:event.target.value as DistributionName})}>{distributions.map((distribution)=><option key={distribution.value} value={distribution.value}>{distribution.label}</option>)}</select></label><label className="risk-enabled"><input type="checkbox" checked={item.enabled} onChange={(event)=>patchItem(item.id,{enabled:event.target.checked})}/>Actif</label><Button aria-label="Dupliquer le poste" onClick={()=>duplicateItem(item)}><Copy/></Button><Button aria-label="Supprimer le poste" onClick={()=>removeItem(item.id)} disabled={register.items.length===1}><Trash2/></Button></div>
        <div className="risk-row-details"><ParameterFields item={item} onChange={(patch)=>patchItem(item.id,patch)}/><label>Catégorie<input value={item.category} onChange={(event)=>patchItem(item.id,{category:event.target.value})}/></label><label>Unité<input value={item.unit} onChange={(event)=>patchItem(item.id,{unit:event.target.value})} placeholder={register.metadata.defaultUnit}/></label><label className="risk-notes">Notes<input value={item.notes} onChange={(event)=>patchItem(item.id,{notes:event.target.value})}/></label></div>
        <div className={`risk-row-status ${issue?'invalid':'valid'}`}>{issue?<><XCircle/>{issue}</>:<><CheckCircle2/>Paramètres cohérents</>}</div>
      </article>})}
    </div>{projectReady&&(activeItems.length===0||localIssues.length>0)?<WorkflowGuidance title={activeItems.length?'Des postes doivent être corrigés':'Ajoutez au moins un poste actif'} detail={activeItems.length?`${localIssues.length} poste(s) contiennent encore des paramètres incomplets ou incohérents.`:'La simulation nécessite au moins une composante incertaine active.'} action={activeItems.length?'Voir les postes':'Ajouter un poste'} onAction={activeItems.length?()=>setTab('items'):addItem}/>:null}<div className="builder-footer"><span>{activeItems.length} poste{activeItems.length>1?'s':''} actif{activeItems.length>1?'s':''} · {localIssues.length?`${localIssues.length} correction(s) locale(s) requise(s)`:'prêt pour le contrôle moteur'}</span><Button variant="primary" disabled={!projectReady||!activeItems.length||localIssues.length>0} onClick={()=>setTab('correlations')}>Configurer les corrélations</Button></div></Card>:null}

    {tab==='correlations'?<Card className="register-builder-card correlation-card"><CardTitle info={false}><span className="title-with-icon"><Grid3X3/>Dépendances entre postes</span></CardTitle>{(!projectReady||!activeItems.length||localIssues.length>0)?<WorkflowGuidance title="Les étapes précédentes ne sont pas terminées" detail={!projectReady?'Complétez d’abord l’identité du projet.':'Corrigez ou ajoutez les postes actifs avant de définir leurs dépendances.'} action={!projectReady?'Aller au projet':'Aller aux postes'} onAction={()=>setTab(!projectReady?'project':'items')}/>:null}<div className="correlation-choice"><label className={register.correlations.mode==='independent'?'selected':''}><input type="radio" checked={register.correlations.mode==='independent'} onChange={()=>setCorrelationMode('independent')} disabled={!projectReady||!activeItems.length}/><b>Postes indépendants</b><span>Aucune dépendance statistique n’est appliquée.</span></label><label className={register.correlations.mode==='correlated'?'selected':''}><input type="radio" checked={register.correlations.mode==='correlated'} onChange={()=>setCorrelationMode('correlated')} disabled={!projectReady||!activeItems.length}/><b>Matrice de corrélation</b><span>Définissez les coefficients entre −1 et 1.</span></label></div>
      {register.correlations.mode==='correlated'?<div className="correlation-table-wrap"><table className="correlation-table"><thead><tr><th>Poste</th>{register.correlations.names.map((name)=><th key={name} title={name}>{name}</th>)}</tr></thead><tbody>{register.correlations.names.map((name,row)=><tr key={name}><th>{name}</th>{register.correlations.names.map((columnName,column)=><td key={columnName}><input aria-label={`Corrélation ${name} / ${columnName}`} type="number" min="-1" max="1" step="0.05" value={register.correlations.values[row]?.[column]??0} disabled={row===column} onChange={(event)=>changeCoefficient(row,column,Math.max(-1,Math.min(1,Number(event.target.value))))}/></td>)}</tr>)}</tbody></table><p>La matrice reste symétrique automatiquement. Le moteur vérifie aussi qu’elle est strictement définie positive.</p></div>:<div className="independence-note"><CheckCircle2/><div><b>Hypothèse d’indépendance sélectionnée</b><span>Aucune feuille de corrélation ne sera ajoutée au classeur Excel.</span></div></div>}
      <div className="builder-footer"><span>{activeItems.length} poste{activeItems.length>1?'s':''} concerné{activeItems.length>1?'s':''}.</span><Button variant="primary" onClick={()=>void validate()} disabled={busy||!canValidate}>{busy?'Validation…':'Valider le registre'}</Button></div></Card>:null}

    {tab==='validation'?<div className="validation-layout"><Card className="register-builder-card"><CardTitle info={false}>Contrôle de préparation</CardTitle><div className="validation-summary"><div className={projectReady?'pass':'fail'}>{projectReady?<CheckCircle2/>:<XCircle/>}<span><b>Projet identifié</b><small>{projectReady?register.metadata.projectName:'Nom ou unité manquant'}</small></span></div><div className={activeItems.length&&localIssues.length===0?'pass':'fail'}>{activeItems.length&&localIssues.length===0?<CheckCircle2/>:<XCircle/>}<span><b>Postes actifs cohérents</b><small>{activeItems.length} poste(s), {localIssues.length} anomalie(s) locale(s)</small></span></div><div className={validation?'pass':'pending'}>{validation?<CheckCircle2/>:<Grid3X3/>}<span><b>Validation du moteur</b><small>{validation?'Schéma Excel et règles métier conformes':'À lancer depuis l’étape 3 — Corrélations'}</small></span></div></div>{!validation?<WorkflowGuidance title={!projectReady?'Le projet doit être complété':activeItems.length===0||localIssues.length?'Les postes doivent être corrigés':'La validation finale reste à lancer'} detail={!projectReady?'Le nom du projet et son unité sont obligatoires.':activeItems.length===0||localIssues.length?'Ajoutez au moins un poste actif et corrigez ses paramètres.':'Revenez à l’étape Corrélations, confirmez l’indépendance ou la matrice, puis cliquez sur « Valider le registre ».'} action={!projectReady?'Aller au projet':activeItems.length===0||localIssues.length?'Aller aux postes':'Aller aux corrélations'} onAction={()=>setTab(!projectReady?'project':activeItems.length===0||localIssues.length?'items':'correlations')}/>:null}{validation?<div className="engine-validation"><StatusPill>Registre valide</StatusPill><dl><div><dt>Postes actifs</dt><dd>{validation.activeItems}</dd></div><div><dt>Postes totaux</dt><dd>{validation.totalItems}</dd></div><div><dt>Corrélations</dt><dd>{validation.correlationsEnabled?'Activées':'Indépendance'}</dd></div></dl></div>:null}<div className="builder-footer"><Button onClick={()=>void validate()} disabled={busy||!canValidate}>{busy?'Validation…':'Relancer les contrôles'}</Button><div><Button onClick={()=>void exportExcel()} disabled={busy||!canValidate}>Télécharger Excel</Button><Button variant="primary" aria-describedby={!validation?'simulation-lock-help':undefined} disabled={!validation||busy} onClick={()=>navigate('/configuration')}>Configurer la simulation</Button></div></div>{!validation?<p className="button-lock-help" id="simulation-lock-help">La configuration sera accessible après la validation du registre. Utilisez l’indication ci-dessus pour rejoindre l’étape attendue.</p>:null}</Card></div>:null}
  </>;
}
