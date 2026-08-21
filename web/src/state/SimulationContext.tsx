import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ProjectSource, RiskRegisterDraft, SavedScenario, SimulationResponse, SimulationWorkspaceConfig } from '../types';

const REFERENCE_STORAGE_KEY = 'risksim.reference.v1';
const WORKSPACE_STORAGE_KEY = 'risksim.workspace.v1';
const RESULT_STORAGE_KEY = 'risksim.result.v1';

type StoredReference = { version: 1; result: SimulationResponse };
type StoredResult = { version: 1; result: SimulationResponse };
type StoredWorkspace = {version:1;register:RiskRegisterDraft;config:SimulationWorkspaceConfig;scenarios:SavedScenario[];projectSource?:ProjectSource};
type SimulationState = {
  result: SimulationResponse | null;
  reference: SimulationResponse | null;
  register: RiskRegisterDraft;
  projectSource: ProjectSource;
  config: SimulationWorkspaceConfig;
  scenarios: SavedScenario[];
  setResult: (value: SimulationResponse | null) => void;
  setRegister: (value: RiskRegisterDraft) => void;
  startNewProject: () => void;
  importProject: (value: RiskRegisterDraft) => void;
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

function readResult(): SimulationResponse | null {
  try {
    const raw = window.sessionStorage.getItem(RESULT_STORAGE_KEY);
    if (!raw) return null;
    const stored = JSON.parse(raw) as StoredResult;
    return stored.version === 1 ? stored.result : null;
  } catch {
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    return null;
  }
}

const initialRegister:RiskRegisterDraft={
  schemaVersion:'1.0',
  metadata:{projectName:'',analysisType:'cost',defaultUnit:'',baselineEstimate:null,description:''},
  items:[],
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
  const [result, setResultState] = useState<SimulationResponse | null>(readResult);
  const [reference, setReference] = useState<SimulationResponse | null>(readReference);
  const [register,setRegisterState]=useState<RiskRegisterDraft>(stored?.register??initialRegister);
  const [projectSource,setProjectSource]=useState<ProjectSource>(stored?.projectSource??(stored&&(stored.register.metadata.projectName.trim()||stored.register.items.length)?'new':null));
  const [config,setConfig]=useState<SimulationWorkspaceConfig>(stored?.config??initialConfig);
  const [scenarios,setScenarios]=useState<SavedScenario[]>(stored?.scenarios??[]);

  useEffect(()=>{
    const value:StoredWorkspace={version:1,register,config,scenarios,projectSource};
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY,JSON.stringify(value));
  },[config,projectSource,register,scenarios]);

  const setRegister=useCallback((value:RiskRegisterDraft)=>setRegisterState(value),[]);

  const startNewProject=useCallback(()=>{
    setRegisterState(structuredClone(initialRegister));
    setConfig(structuredClone(initialConfig));
    setProjectSource('new');
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    setResultState(null);
  },[]);

  const importProject=useCallback((value:RiskRegisterDraft)=>{
    setRegisterState(value);
    setProjectSource('imported');
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    setResultState(null);
  },[]);

  const setResult = useCallback((next: SimulationResponse | null) => {
    if (next) {
      const stored: StoredResult = { version: 1, result: next };
      window.sessionStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify(stored));
    } else {
      window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    }
    setResultState(next);
  }, []);

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
    setRegisterState(structuredClone(scenario.register));
    setConfig(structuredClone(scenario.config));
    setProjectSource('new');
  },[scenarios]);

  const deleteScenario=useCallback((id:string)=>setScenarios((current)=>current.filter((item)=>item.id!==id)),[]);

  const value = useMemo(
    () => ({ result, reference, register, projectSource, config, scenarios, setResult, setRegister, startNewProject, importProject, setConfig, saveScenario, loadScenario, deleteScenario, freezeReference, clearReference }),
    [clearReference, config, deleteScenario, freezeReference, importProject, loadScenario, projectSource, reference, register, result, saveScenario, scenarios, setRegister, startNewProject],
  );
  return <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>;
}

export function useSimulation() {
  const value = useContext(SimulationContext);
  if (!value) throw new Error('useSimulation doit être utilisé dans SimulationProvider');
  return value;
}
