import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AccessGate } from './components/access/AccessGate';
import { AccessProvider } from './state/AccessContext';
import { SimulationProvider } from './state/SimulationContext';
import { ThemeProvider } from './state/ThemeContext';
import './styles/global.css';
import './styles/workspace.css';
import './styles/enhancements.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AccessProvider>
          <AccessGate>
            <SimulationProvider><App /></SimulationProvider>
          </AccessGate>
        </AccessProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
