import type { RegisterValidation, RiskRegisterDraft, SimulationConfig, SimulationResponse, SimulationWorkspaceConfig } from '../types';

async function apiError(response:Response,fallback:string){
  const payload=await response.json().catch(()=>null) as {detail?:string}|null;
  return new Error(payload?.detail??fallback);
}

async function simulate(file: File, config: SimulationConfig): Promise<SimulationResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('simulations', String(config.simulations));
  form.append('seed', String(config.seed));
  form.append('confidence_levels', config.levels.map((level) => level / 100).join(','));
  const response = await fetch('/api/simulate', { method: 'POST', body: form });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `La simulation a échoué (${response.status}).`);
  }
  return response.json() as Promise<SimulationResponse>;
}

async function importRegister(file:File):Promise<RiskRegisterDraft>{
  const form=new FormData();form.append('file',file);
  const response=await fetch('/api/register/import',{method:'POST',body:form});
  if(!response.ok)throw await apiError(response,`L’import a échoué (${response.status}).`);
  const payload=await response.json() as {register:RiskRegisterDraft};
  return payload.register;
}

async function validateRegister(register:RiskRegisterDraft):Promise<RegisterValidation>{
  const response=await fetch('/api/register/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(register)});
  if(!response.ok)throw await apiError(response,`La validation a échoué (${response.status}).`);
  return response.json() as Promise<RegisterValidation>;
}

async function exportRegister(register:RiskRegisterDraft):Promise<Blob>{
  const response=await fetch('/api/register/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(register)});
  if(!response.ok)throw await apiError(response,`L’export a échoué (${response.status}).`);
  return response.blob();
}

async function simulateDraft(register:RiskRegisterDraft,config:SimulationWorkspaceConfig):Promise<SimulationResponse>{
  const response=await fetch('/api/register/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({register,config})});
  if(!response.ok)throw await apiError(response,`La simulation a échoué (${response.status}).`);
  return response.json() as Promise<SimulationResponse>;
}

async function exportResults(
  result: SimulationResponse,
  register: RiskRegisterDraft,
  config: SimulationWorkspaceConfig,
): Promise<Blob> {
  const response = await fetch('/api/results/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result, register, config }),
  });
  if (!response.ok) throw await apiError(response, `L’export des résultats a échoué (${response.status}).`);
  return response.blob();
}

async function exportResultsBundle(
  result: SimulationResponse,
  register: RiskRegisterDraft,
  config: SimulationWorkspaceConfig,
): Promise<Blob> {
  const response = await fetch('/api/results/export-bundle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result, register, config }),
  });
  if (!response.ok) throw await apiError(response, `Le dossier ZIP n’a pas pu être généré (${response.status}).`);
  return response.blob();
}

export const simulationService = {
  simulate,
  importRegister,
  validateRegister,
  exportRegister,
  exportResults,
  exportResultsBundle,
  simulateDraft,
};
