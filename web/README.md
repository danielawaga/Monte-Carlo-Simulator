# Interface web RiskSim

Interface React, TypeScript et Vite du simulateur Monte Carlo. Le parcours principal suit `/risques` (préparation du registre), `/configuration` (simulation et scénarios), puis `/resultats`.

## Démarrage intégré

Depuis la racine du dépôt, démarrez l'API Python :

```bash
./.python/python.exe -m pip install -e ".[web]"
./.python/python.exe -m uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

Dans un second terminal Git Bash :

```bash
cd web
npm install
npm run dev
```

Ouvrez ensuite `http://localhost:5173/risques`. Vous pouvez construire le registre dans l'interface ou importer un `.xlsx`, le valider, l'exporter, puis poursuivre vers la simulation. Vite relaie automatiquement les requêtes `/api` vers le moteur Python sur le port 8000.

## État de l'intégration S6

- le registre, la configuration et les résultats principaux utilisent le moteur Python réel ;
- le constructeur prend en charge les métadonnées du projet, les six distributions, les postes actifs et la matrice de corrélation ;
- l'import, la validation, l'export Excel et la simulation d'un brouillon JSON passent par l'API ;
- l'histogramme, la S-curve et la sensibilité utilisent les artefacts du run courant ;
- le moteur conserve les corrélations présentes dans le registre Excel ;
- les scénarios sont enregistrés avec une copie du registre et de la configuration dans l'onglet Scénarios de `/configuration` ;
- un run peut toujours être figé comme référence dans le navigateur et comparé au run suivant ;
- les vues de pilotage s’appuient sur les données locales réellement enregistrées par l’application ;
- `src/services/simulationService.ts` constitue le contrat d'adaptation entre React et Python.

Pour produire la version optimisée :

```bash
npm run build
npm run preview
```
