import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import App from '../../App';
import { AuthProvider } from '../../state/AuthContext';
import { SimulationProvider } from '../../state/SimulationContext';
import { ThemeProvider } from '../../state/ThemeContext';

function renderApp() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <ThemeProvider>
        <AuthProvider>
          <SimulationProvider><App /></SimulationProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>,
  );
}

describe('AppShell', () => {
  it('mémorise le thème et l’état rétracté du panneau latéral', async () => {
    const user = userEvent.setup();
    const { container } = renderApp();

    await user.click(screen.getByRole('button', { name: 'Thème Sombre' }));
    await waitFor(() => expect(document.documentElement.dataset.theme).toBe('dark'));
    expect(JSON.parse(String(window.localStorage.getItem('risksim.theme.v1')))).toEqual({
      version: 1,
      preference: 'dark',
    });

    await user.click(screen.getByRole('button', { name: 'Réduire le panneau latéral' }));
    expect(container.querySelector('.shell')).toHaveClass('sidebar-collapsed');
    expect(JSON.parse(String(window.localStorage.getItem('risksim.shell.v1')))).toEqual({
      version: 1,
      collapsed: true,
    });
    expect(screen.getByRole('button', { name: 'Déployer le panneau latéral' })).toBeVisible();
  });
});
