import { apiFetch } from './authSession';
import type {
  RiskRegisterDraft,
  SharedRegister,
  SharedRun,
  SimulationResponse,
  SimulationWorkspaceConfig,
} from '../types';

async function detail(response: Response, fallback: string): Promise<string> {
  const payload = await response.json().catch(() => null) as { detail?: string } | null;
  return payload?.detail ?? fallback;
}

/** Every register held by this installation — the team shares them all. */
export async function listSharedRegisters(): Promise<SharedRegister[]> {
  const response = await apiFetch('/api/registers');
  if (!response.ok) throw new Error(await detail(response, 'Les registres partagés sont indisponibles.'));
  const payload = await response.json() as { registers: SharedRegister[] };
  return payload.registers;
}

/**
 * Publish a register. Passing `registerId` overwrites the shared copy, which is
 * how a colleague continues someone else's work; the server keeps the original
 * author and records who touched it last.
 */
export async function saveSharedRegister(
  name: string,
  register: RiskRegisterDraft,
  registerId?: number,
): Promise<SharedRegister> {
  const response = await apiFetch('/api/registers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, register, registerId }),
  });
  if (!response.ok) throw new Error(await detail(response, 'L’enregistrement a échoué.'));
  const payload = await response.json() as { register: SharedRegister };
  return payload.register;
}

/** Administrators only — the server enforces it. */
export async function deleteSharedRegister(registerId: number): Promise<void> {
  const response = await apiFetch(`/api/registers/${registerId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(await detail(response, 'La suppression a échoué.'));
}

export async function listSharedRuns(registerId?: number): Promise<SharedRun[]> {
  const query = registerId === undefined ? '' : `?register_id=${registerId}`;
  const response = await apiFetch(`/api/runs${query}`);
  if (!response.ok) throw new Error(await detail(response, 'L’historique est indisponible.'));
  const payload = await response.json() as { runs: SharedRun[] };
  return payload.runs;
}

/** Keep a completed simulation, so a figure sent to a client can be traced back. */
export async function saveSharedRun(
  label: string,
  config: SimulationWorkspaceConfig,
  result: SimulationResponse,
  registerId?: number,
): Promise<SharedRun> {
  const response = await apiFetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label, config, result, registerId }),
  });
  if (!response.ok) throw new Error(await detail(response, 'L’enregistrement de l’exécution a échoué.'));
  const payload = await response.json() as { run: SharedRun };
  return payload.run;
}
