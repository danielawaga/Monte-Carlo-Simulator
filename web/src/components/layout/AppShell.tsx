import { Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../navigation/Sidebar';

type StoredShell = { version: 1; collapsed: boolean };

const SHELL_STORAGE_KEY = 'risksim.shell.v1';

function readCollapsed() {
  try {
    const raw = window.localStorage.getItem(SHELL_STORAGE_KEY);
    if (!raw) return false;
    const stored = JSON.parse(raw) as StoredShell;
    return stored.version === 1 ? stored.collapsed : false;
  } catch {
    window.localStorage.removeItem(SHELL_STORAGE_KEY);
    return false;
  }
}

export function AppShell() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, [location.pathname]);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((current) => {
      const next = !current;
      const stored: StoredShell = { version: 1, collapsed: next };
      window.localStorage.setItem(SHELL_STORAGE_KEY, JSON.stringify(stored));
      return next;
    });
  }, []);

  return (
    <div className={`shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <header className="mobile-shellbar">
        <button type="button" onClick={() => setMobileOpen(true)} aria-label="Ouvrir le menu principal"><Menu /></button>
        <strong>RiskSim</strong><span>Monte Carlo</span>
      </header>
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onNavigate={() => setMobileOpen(false)}
        onMobileClose={() => setMobileOpen(false)}
      />
      <button
        type="button"
        className={`sidebar-backdrop ${mobileOpen ? 'visible' : ''}`}
        aria-label="Fermer le menu en cliquant hors du panneau"
        onClick={() => setMobileOpen(false)}
      />
      <main className="main">
        <button
          type="button"
          className="main-sidebar-toggle"
          onClick={toggleCollapsed}
          aria-label={collapsed ? 'Déployer le panneau latéral' : 'Réduire le panneau latéral'}
          title={collapsed ? 'Déployer le panneau latéral' : 'Réduire le panneau latéral'}
        >
          {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
        </button>
        <Outlet />
      </main>
    </div>
  );
}
