import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { SimulationProvider } from './state/SimulationContext';
import { ThemeProvider } from './state/ThemeContext';
import './styles/tokens.css';
import './styles/global.css';
import './styles/workspace.css';
import './styles/enhancements.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider><SimulationProvider><App /></SimulationProvider></ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
