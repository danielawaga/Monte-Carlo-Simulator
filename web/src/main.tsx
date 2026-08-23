import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthGate } from './components/auth/AuthGate';
import { AuthProvider } from './state/AuthContext';
import { SimulationProvider } from './state/SimulationContext';
import { ThemeProvider } from './state/ThemeContext';
import './styles/global.css';
import './styles/workspace.css';
import './styles/enhancements.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AuthGate>
            <SimulationProvider><App /></SimulationProvider>
          </AuthGate>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
