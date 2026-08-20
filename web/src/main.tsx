import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { SimulationProvider } from './state/SimulationContext';
import './styles/global.css';
import './styles/workspace.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <SimulationProvider><App /></SimulationProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
