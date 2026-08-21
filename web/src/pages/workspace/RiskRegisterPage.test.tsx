import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SimulationProvider } from '../../state/SimulationContext';
import { riskRegisterFixture } from '../../test/simulationFixture';
import { RiskRegisterPage } from './RiskRegisterPage';

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/risques']}>
      <SimulationProvider><RiskRegisterPage /></SimulationProvider>
    </MemoryRouter>,
  );
}

describe('RiskRegisterPage', () => {
  it('demande de créer ou importer un projet avant d’afficher son identité', async () => {
    const user = userEvent.setup();
    renderRegister();

    expect(screen.getByRole('heading', { name: 'Commencer un registre de risques' })).toBeVisible();
    expect(screen.queryByText('Identité et cadre de l’analyse')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Créer un nouveau projet/i }));
    expect(screen.getByText('Identité et cadre de l’analyse')).toBeVisible();
    expect(screen.getByLabelText('Nom du projet')).toHaveAttribute(
      'placeholder',
      'Ex. Extension de l’usine de Casablanca',
    );
    expect(screen.getByRole('button', { name: 'Continuer vers les postes' })).toBeDisabled();
    expect(screen.getByText('Deux renseignements sont encore nécessaires')).toBeVisible();
  });

  it('préremplit le projet importé et explique comment lever le blocage de validation', async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ register: riskRegisterFixture }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    renderRegister();

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, new File(['xlsx'], 'registre.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
    expect(await screen.findByDisplayValue('Projet importé')).toBeVisible();
    expect(screen.getByDisplayValue('MAD')).toBeVisible();

    await user.click(screen.getByRole('tab', { name: /Validation/ }));
    expect(screen.getByText('La validation finale reste à lancer')).toBeVisible();
    expect(screen.getByRole('button', { name: /Aller aux corrélations/i })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Configurer la simulation' })).toBeDisabled();
  });
});
