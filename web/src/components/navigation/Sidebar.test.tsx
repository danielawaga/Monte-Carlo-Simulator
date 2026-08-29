import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '../../state/ThemeContext';
import { Sidebar } from './Sidebar';

function renderSidebar() {
  return render(
    <MemoryRouter>
      <ThemeProvider>
        <Sidebar collapsed={false} mobileOpen={false} onNavigate={() => undefined} onMobileClose={() => undefined} />
      </ThemeProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Sidebar shutdown control', () => {
  it('asks for confirmation before stopping the packaged server', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const fetchMock = vi.spyOn(window, 'fetch');
    renderSidebar();

    await user.click(screen.getByRole('button', { name: 'Quitter RiskSim' }));

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('confirms that the portable directory can be released', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.spyOn(window, 'fetch').mockResolvedValue({ ok: true } as Response);
    renderSidebar();

    await user.click(screen.getByRole('button', { name: 'Quitter RiskSim' }));

    expect(window.fetch).toHaveBeenCalledWith('/api/shutdown', { method: 'POST' });
    expect(await screen.findByRole('dialog', { name: 'RiskSim est arrêté' })).toBeVisible();
  });
});
