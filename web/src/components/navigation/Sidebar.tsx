import { useState } from 'react';
import {
  BarChart3,
  ChevronDown,
  CircleHelp,
  ClipboardList,
  Home,
  Settings,
  SlidersHorizontal,
  Users,
} from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';

const Logo = () => (
  <NavLink className="brand" to="/" aria-label="RiskSim — Accueil">
    <svg viewBox="0 0 48 42" aria-hidden="true">
      <path d="M3 35 15 21l9 8L43 5M3 23l12-15 10 10L42 1" />
      <circle cx="3" cy="35" r="2" />
      <circle cx="15" cy="21" r="2" />
      <circle cx="24" cy="29" r="2" />
      <circle cx="43" cy="5" r="2" />
    </svg>
    <div>
      <strong>RiskSim</strong>
      <span>Monte Carlo</span>
    </div>
  </NavLink>
);

export function Sidebar() {
  const { pathname } = useLocation();
  const simulationActive = pathname === '/configuration' || pathname === '/scenarios';
  const [simulationOpen, setSimulationOpen] = useState(simulationActive);

  return (
    <aside className="sidebar">
      <Logo />
      <nav aria-label="Navigation principale">
        <NavLink className="nav-main" to="/" end>
          <Home />
          Accueil
        </NavLink>
        <NavLink className="nav-main" to="/risques">
          <ClipboardList />
          Registre de risques
        </NavLink>
        <button
          className={`nav-parent ${simulationActive ? 'parent-active' : ''}`}
          type="button"
          aria-expanded={simulationOpen}
          aria-controls="simulation-navigation"
          onClick={() => setSimulationOpen((open) => !open)}
        >
          <SlidersHorizontal />
          <span>Simulation</span>
          <ChevronDown className={simulationOpen ? 'chevron-open' : ''} />
        </button>
        {simulationOpen ? (
          <div className="subnav" id="simulation-navigation">
            <NavLink to="/configuration">
              <i />
              Configuration
            </NavLink>
            <NavLink to="/scenarios">
              <i />
              Scénarios
            </NavLink>
          </div>
        ) : null}
        <NavLink className="nav-main" to="/resultats">
          <BarChart3 />
          Résultats
        </NavLink>
        <NavLink className="nav-main" to="/parametres">
          <Settings />
          Paramètres
        </NavLink>
        <NavLink className="nav-main" to="/administration">
          <Users />
          Administration
        </NavLink>
      </nav>
      <div className="sidebar-bottom">
        <NavLink className="nav-main help-link" to="/aide">
          <CircleHelp />
          Aide &amp; documentation
        </NavLink>
        <NavLink className="user user-link" to="/profil">
          <span>PD</span>
          <div>
            <strong>Pierre Dubois</strong>
            <small>Chef de projet</small>
          </div>
          <ChevronDown />
        </NavLink>
      </div>
    </aside>
  );
}
