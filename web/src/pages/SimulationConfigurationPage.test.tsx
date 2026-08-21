import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { SimulationProvider } from '../state/SimulationContext';
import { SimulationConfigurationPage } from './SimulationConfigurationPage';

describe('SimulationConfigurationPage', () => {
  it('redirige clairement vers le registre lorsqu’aucun projet n’existe', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/configuration']}>
        <SimulationProvider>
          <Routes>
            <Route path="/configuration" element={<SimulationConfigurationPage />} />
            <Route path="/risques" element={<h1>Registre cible</h1>} />
          </Routes>
        </SimulationProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText('Commencez par créer ou importer un projet')).toBeVisible();
    await user.click(screen.getByRole('button', { name: /Ouvrir le registre de risques/i }));
    expect(screen.getByRole('heading', { name: 'Registre cible' })).toBeVisible();
  });
});
