import {
  BarChart3,
  ChevronDown,
  CircleHelp,
  ClipboardList,
  Dices,
  Home,
  LockKeyhole,
  Monitor,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Sun,
  Users,
  X,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../state/AuthContext';
import { useTheme, type ThemePreference } from '../../state/ThemeContext';

function initials(fullName: string | undefined): string {
  if (!fullName) return '··';
  const parts = fullName.trim().split(/\s+/).slice(0, 2);
  return parts.map((part) => part[0]?.toUpperCase() ?? '').join('') || '··';
}

const Logo = ({ collapsed, onNavigate }: { collapsed: boolean; onNavigate: () => void }) => (
  <NavLink className="brand" to="/" aria-label="RiskSim — Accueil" onClick={onNavigate}>
    <svg viewBox="0 0 48 42" aria-hidden="true">
      <path d="M3 35 15 21l9 8L43 5M3 23l12-15 10 10L42 1" />
      <circle cx="3" cy="35" r="2" />
      <circle cx="15" cy="21" r="2" />
      <circle cx="24" cy="29" r="2" />
      <circle cx="43" cy="5" r="2" />
    </svg>
    <div><strong>RiskSim</strong><span>Monte Carlo</span></div>
  </NavLink>
);

const navigation = [
  { to: '/', label: 'Accueil', icon: Home, end: true },
  { to: '/risques', label: 'Registre de risques', icon: ClipboardList },
  { to: '/configuration', label: 'Simulation', icon: Dices },
  { to: '/resultats', label: 'Résultats', icon: BarChart3 },
  { to: '/parametres', label: 'Paramètres', icon: Settings },
  { to: '/administration', label: 'Administration', icon: Users },
] as const;

const themes: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Clair', icon: Sun },
  { value: 'dark', label: 'Sombre', icon: Moon },
  { value: 'system', label: 'Système', icon: Monitor },
];

type SidebarProps = {
  collapsed: boolean;
  mobileOpen: boolean;
  onToggle: () => void;
  onNavigate: () => void;
  onMobileClose: () => void;
};

export function Sidebar({ collapsed, mobileOpen, onToggle, onNavigate, onMobileClose }: SidebarProps) {
  const { theme, setTheme } = useTheme();
  const { user, signOut } = useAuth();

  return (
    <aside className={`sidebar ${collapsed ? 'is-collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-brand-row">
        <Logo collapsed={collapsed} onNavigate={onNavigate} />
        <button className="sidebar-mobile-close" type="button" onClick={onMobileClose} aria-label="Fermer le menu principal"><X /></button>
      </div>
      <button
        type="button"
        className="sidebar-toggle"
        onClick={onToggle}
        aria-label={collapsed ? 'Déployer le panneau latéral' : 'Réduire le panneau latéral'}
        title={collapsed ? 'Déployer le panneau latéral' : 'Réduire le panneau latéral'}
      >
        {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
      </button>
      <nav aria-label="Navigation principale">
        {navigation.map(({ to, label, icon: Icon, ...item }) => (
          <NavLink className="nav-main" to={to} end={'end' in item ? item.end : undefined} key={to} title={collapsed ? label : undefined} onClick={onNavigate}>
            <Icon /><span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="theme-switch" role="group" aria-label="Thème de l’interface">
          {themes.map(({ value, label, icon: Icon }) => (
            <button type="button" className={theme === value ? 'active' : ''} onClick={() => setTheme(value)} aria-label={`Thème ${label}`} title={`Thème ${label}`} key={value}>
              <Icon /><span>{label}</span>
            </button>
          ))}
        </div>
        <button type="button" className="nav-main lock-button" onClick={() => void signOut()} title={collapsed ? 'Se déconnecter' : undefined}>
          <LockKeyhole /><span>Se déconnecter</span>
        </button>
        <NavLink className="nav-main help-link" to="/aide" title={collapsed ? 'Aide & documentation' : undefined} onClick={onNavigate}>
          <CircleHelp /><span>Aide &amp; documentation</span>
        </NavLink>
        <NavLink className="user user-link" to="/profil" title={collapsed ? user?.fullName : undefined} onClick={onNavigate}>
          <span>{initials(user?.fullName)}</span>
          <div><strong>{user?.fullName ?? 'Compte'}</strong><small>{user?.role === 'admin' ? 'Administrateur' : 'Membre'}</small></div>
          <ChevronDown />
        </NavLink>
      </div>
    </aside>
  );
}
