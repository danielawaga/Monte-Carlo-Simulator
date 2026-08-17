# Interface web RiskSim

Interface React, TypeScript et Vite du simulateur Monte Carlo. Les trois parcours sont accessibles aux routes suivantes :

- `/configuration` — préparation d'une simulation ;
- `/resultats` — analyse des résultats ;
- `/scenarios` — comparaison de scénarios.

## Démarrage

```bash
cd web
npm install
npm run dev
```

Pour produire la version optimisée :

```bash
npm run build
npm run preview
```

Les données de démonstration sont isolées dans `src/data/mockSimulation.ts`. Le service `src/services/simulationService.ts` constitue le point d'adaptation à remplacer par les appels au backend Python, sans déplacer de logique probabiliste dans les composants React.
