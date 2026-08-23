import type {
  RiskRegisterDraft,
  SavedRegister,
  SavedRun,
  SimulationResponse,
  SimulationWorkspaceConfig,
} from '../types';

async function detail(response: Response, fallback: string): Promise<string> {
  const payload = await response.json().catch(() => null) as { detail?: string } | null;
  return payload?.detail ?? fallback;
}

/** Every register saved on this installation. */
export async function listRegisters(): Promise<SavedRegister[]> {
  const response = await fetch('/api/registers');
  if (!response.ok) throw new Error(await detail(response, 'Les registres enregistrés sont indisponibles.'));
  const payload = await response.json() as { registers: SavedRegister[] };
  return payload.registers;
}

/**
 * Save a register. Passing `registerId` overwrites an existing one, keeping its
 * original creation date.
 */
export async function saveRegister(
  name: string,
  register: RiskRegisterDraft,
  registerId?: number,
): Promise<SavedRegister> {
  const response = await fetch('/api/registers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, register, registerId }),
  });
  if (!response.ok) throw new Error(await detail(response, 'L’enregistrement a échoué.'));
  const payload = await response.json() as { register: SavedRegister };
  return payload.register;
}

/** Remove a register; the runs produced from it are kept. */
export async function deleteRegister(registerId: number): Promise<void> {
  const response = await fetch(`/api/registers/${registerId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(await detail(response, 'La suppression a échoué.'));
}

export async function listRuns(registerId?: number): Promise<SavedRun[]> {
  const query = registerId === undefined ? '' : `?register_id=${registerId}`;
  const response = await fetch(`/api/runs${query}`);
  if (!response.ok) throw new Error(await detail(response, 'L’historique est indisponible.'));
  const payload = await response.json() as { runs: SavedRun[] };
  return payload.runs;
}

/** Keep a completed simulation, so a figure sent to a client can be traced back. */
export async function saveRun(
  label: string,
  config: SimulationWorkspaceConfig,
  result: SimulationResponse,
  registerId?: number,
): Promise<SavedRun> {
  const response = await fetch('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label, config, result, registerId }),
  });
  if (!response.ok) throw new Error(await detail(response, 'L’enregistrement de l’exécution a échoué.'));
  const payload = await response.json() as { run: SavedRun };
  return payload.run;
}
