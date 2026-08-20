import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { RiskRegisterDraft, SavedScenario, SimulationResponse, SimulationWorkspaceConfig } from '../types';

const REFERENCE_STORAGE_KEY = 'risksim.reference.v1';
const WORKSPACE_STORAGE_KEY = 'risksim.workspace.v1';

type StoredReference = { version: 1; result: SimulationResponse };
type StoredWorkspace = {version:1;register:RiskRegisterDraft;config:SimulationWorkspaceConfig;scenarios:SavedScenario[]};
type SimulationState = {
  result: SimulationResponse | null;
  reference: SimulationResponse | null;
  register: RiskRegisterDraft;
  config: SimulationWorkspaceConfig;
  scenarios: SavedScenario[];
  setResult: (value: SimulationResponse | null) => void;
  setRegister: (value: RiskRegisterDraft) => void;
  setConfig: (value: SimulationWorkspaceConfig) => void;
  saveScenario: () => SavedScenario;
  loadScenario: (id: string) => void;
  deleteScenario: (id: string) => void;
  freezeReference: () => void;
  clearReference: () => void;
};

const SimulationContext = createContext<SimulationState | null>(null);

function readReference(): SimulationResponse | null {
  try {
    const raw = window.localStorage.getItem(REFERENCE_STORAGE_KEY);
    if (!raw) return null;
    const stored = JSON.parse(raw) as StoredReference;
    return stored.version === 1 ? stored.result : null;
  } catch {
    window.localStorage.removeItem(REFERENCE_STORAGE_KEY);
    return null;
  }
}

const initialRegister:RiskRegisterDraft={
  schemaVersion:'1.0',
  metadata:{projectName:'Projet Atlas — Modernisation du SI',analysisType:'cost',defaultUnit:'EUR',baselineEstimate:2_100_000,description:'Analyse probabiliste des coûts du projet.'},
  items:[
    {id:'risk-1',name:'Études détaillées',distribution:'triangular',minimum:120_000,mostLikely:165_000,maximum:240_000,mean:null,standardDeviation:null,probability:null,impact:null,lambdaShape:null,category:'Ingénierie',unit:'EUR',enabled:true,notes:'Estimation à trois points.'},
    {id:'risk-2',name:'Retard fournisseur',distribution:'event',minimum:null,mostLikely:null,maximum:null,mean:null,standardDeviation:null,probability:.25,impact:320_000,lambdaShape:null,category:'Fournisseurs',unit:'EUR',enabled:true,notes:'Impact si le risque survient.'},
    {id:'risk-3',name:'Prix des équipements',distribution:'pert',minimum:400_000,mostLikely:520_000,maximum:760_000,mean:null,standardDeviation:null,probability:null,impact:null,lambdaShape:4,category:'Marché',unit:'EUR',enabled:true,notes:'Estimation PERT.'},
  ],
  correlations:{mode:'independent',names:[],values:[]},
};

const initialConfig:SimulationWorkspaceConfig={simulations:50_000,seed:20260820,levels:[50,80,90,95],decisionPercentile:80,exceedanceThreshold:3_000_000,convergenceTolerance:1,samplingMethod:'pseudo-random',scenarioName:'Scénario de référence',scenarioDescription:'Configuration de base du projet.'};

function readWorkspace():StoredWorkspace|null{
  try{
    const raw=window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
    if(!raw)return null;
    const stored=JSON.parse(raw) as StoredWorkspace;
    return stored.version===1?stored:null;
  }catch{
    window.localStorage.removeItem(WORKSPACE_STORAGE_KEY);
    return null;
  }
}

export function SimulationProvider({ children }: { children: ReactNode }) {
  const stored=useMemo(readWorkspace,[]);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [reference, setReference] = useState<SimulationResponse | null>(readReference);
  const [register,setRegister]=useState<RiskRegisterDraft>(stored?.register??initialRegister);
  const [config,setConfig]=useState<SimulationWorkspaceConfig>(stored?.config??initialConfig);
  const [scenarios,setScenarios]=useState<SavedScenario[]>(stored?.scenarios??[]);

  useEffect(()=>{
    const value:StoredWorkspace={version:1,register,config,scenarios};
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY,JSON.stringify(value));
  },[config,register,scenarios]);

  const freezeReference = useCallback(() => {
    if (!result) return;
    const stored: StoredReference = { version: 1, result };
    window.localStorage.setItem(REFERENCE_STORAGE_KEY, JSON.stringify(stored));
    setReference(result);
  }, [result]);

  const clearReference = useCallback(() => {
    window.localStorage.removeItem(REFERENCE_STORAGE_KEY);
    setReference(null);
  }, []);

  const saveScenario=useCallback(()=>{
    const scenario:SavedScenario={id:`scenario-${Date.now()}`,name:config.scenarioName.trim()||'Scénario sans nom',description:config.scenarioDescription,savedAt:new Date().toISOString(),config:structuredClone(config),register:structuredClone(register)};
    setScenarios((current)=>[scenario,...current]);
    return scenario;
  },[config,register]);

  const loadScenario=useCallback((id:string)=>{
    const scenario=scenarios.find((item)=>item.id===id);
    if(!scenario)return;
    setRegister(structuredClone(scenario.register));
    setConfig(structuredClone(scenario.config));
  },[scenarios]);

  const deleteScenario=useCallback((id:string)=>setScenarios((current)=>current.filter((item)=>item.id!==id)),[]);

  const value = useMemo(
    () => ({ result, reference, register, config, scenarios, setResult, setRegister, setConfig, saveScenario, loadScenario, deleteScenario, freezeReference, clearReference }),
    [clearReference, config, deleteScenario, freezeReference, loadScenario, reference, register, result, saveScenario, scenarios],
  );
  return <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>;
}

export function useSimulation() {
  const value = useContext(SimulationContext);
  if (!value) throw new Error('useSimulation doit être utilisé dans SimulationProvider');
  return value;
}
