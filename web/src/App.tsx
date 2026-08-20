import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ScenarioComparisonPage } from './pages/ScenarioComparisonPage';
import { SimulationConfigurationPage } from './pages/SimulationConfigurationPage';
import { SimulationResultsPage } from './pages/SimulationResultsPage';
import { AdministrationPage } from './pages/workspace/AdministrationPage';
import { DashboardPage } from './pages/workspace/DashboardPage';
import { HelpPage } from './pages/workspace/HelpPage';
import { ProfilePage } from './pages/workspace/ProfilePage';
import { RiskRegisterPage } from './pages/workspace/RiskRegisterPage';
import { SettingsPage } from './pages/workspace/SettingsPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="/risques" element={<RiskRegisterPage />} />
        <Route path="/configuration" element={<SimulationConfigurationPage />} />
        <Route path="/resultats" element={<SimulationResultsPage />} />
        <Route path="/scenarios" element={<Navigate to="/configuration?tab=scenarios" replace />} />
        <Route path="/comparaison" element={<ScenarioComparisonPage />} />
        <Route path="/parametres" element={<SettingsPage />} />
        <Route path="/administration" element={<AdministrationPage />} />
        <Route path="/aide" element={<HelpPage />} />
        <Route path="/profil" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
