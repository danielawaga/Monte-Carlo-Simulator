import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ProjectSource, RiskRegisterDraft, SavedScenario, SimulationResponse, SimulationWorkspaceConfig } from '../types';

const REFERENCE_STORAGE_KEY = 'risksim.reference.v1';
const WORKSPACE_STORAGE_KEY = 'risksim.workspace.v1';
const RESULT_STORAGE_KEY = 'risksim.result.v1';

type StoredReference = { version: 1; result: SimulationResponse };
type StoredResult = { version: 1; result: SimulationResponse };
type StoredWorkspace = {version:1;register:RiskRegisterDraft;config:SimulationWorkspaceConfig;scenarios:SavedScenario[];projectSource?:ProjectSource;importedRegister?:RiskRegisterDraft|null;savedRegisterId?:number|null};
type SimulationState = {
  result: SimulationResponse | null;
  reference: SimulationResponse | null;
  register: RiskRegisterDraft;
  projectSource: ProjectSource;
  config: SimulationWorkspaceConfig;
  scenarios: SavedScenario[];
  /** True while an imported register is available to fall back on. */
  canResetToImported: boolean;
  /** Which saved register the current draft came from, so runs link back to it. */
  savedRegisterId: number | null;
  setSavedRegisterId: (value: number | null) => void;
  setResult: (value: SimulationResponse | null) => void;
  setRegister: (value: RiskRegisterDraft) => void;
  startNewProject: () => void;
  importProject: (value: RiskRegisterDraft) => void;
  resetToImported: () => void;
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
  const [importedRegister,setImportedRegister]=useState<RiskRegisterDraft|null>(stored?.importedRegister??null);
  const [savedRegisterId,setSavedRegisterId]=useState<number|null>(stored?.savedRegisterId??null);

  useEffect(()=>{
    const value:StoredWorkspace={version:1,register,config,scenarios,projectSource,importedRegister,savedRegisterId};
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY,JSON.stringify(value));
  },[config,importedRegister,projectSource,register,scenarios,savedRegisterId]);

  const setRegister=useCallback((value:RiskRegisterDraft)=>setRegisterState(value),[]);

  const startNewProject=useCallback(()=>{
    setRegisterState(structuredClone(initialRegister));
    setConfig(structuredClone(initialConfig));
    setProjectSource('new');
    setImportedRegister(null);
    setSavedRegisterId(null);
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    setResultState(null);
  },[]);

  const importProject=useCallback((value:RiskRegisterDraft)=>{
    setRegisterState(value);
    // Keep the imported workbook aside so edited assumptions can be rolled back to it.
    setImportedRegister(structuredClone(value));
    setSavedRegisterId(null);
    setProjectSource('imported');
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    setResultState(null);
  },[]);

  const resetToImported=useCallback(()=>{
    if(!importedRegister)return;
    setRegisterState(structuredClone(importedRegister));
    // The stored result was produced by the edited assumptions: it no longer matches.
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY);
    setResultState(null);
  },[importedRegister]);

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
    () => ({ result, reference, register, projectSource, config, scenarios, canResetToImported: importedRegister !== null && projectSource === 'imported', savedRegisterId, setSavedRegisterId, setResult, setRegister, startNewProject, importProject, resetToImported, setConfig, saveScenario, loadScenario, deleteScenario, freezeReference, clearReference }),
    [clearReference, config, deleteScenario, freezeReference, importProject, importedRegister, loadScenario, projectSource, reference, register, resetToImported, result, saveScenario, scenarios, setRegister, savedRegisterId, startNewProject],
  );
  return <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>;
}

export function useSimulation() {
  const value = useContext(SimulationContext);
  if (!value) throw new Error('useSimulation doit être utilisé dans SimulationProvider');
  return value;
}
