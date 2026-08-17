# S5 — migration de l'interface vers React / TypeScript

## Pourquoi faire évoluer Streamlit ?

L'interface Streamlit de S4 a validé le parcours fonctionnel : chargement du registre, configuration, simulation et lecture des résultats. En S5, la difficulté n'est plus de démontrer que le moteur peut être utilisé sans code, mais de mieux hiérarchiser l'information et de préparer les interactions de comparaison de scénarios.

La migration ne remplace donc pas le moteur Python. Elle sépare plus nettement :

- **le domaine et les calculs**, conservés dans `src/monte_carlo_simulator` ;
- **l'adaptation HTTP**, assurée par `monte_carlo_simulator.web_api` ;
- **la présentation**, réalisée dans `web/` avec React, TypeScript et Vite.

## Architecture

```text
Navigateur React / TypeScript
          |
          | multipart/form-data + JSON
          v
FastAPI — src/monte_carlo_simulator/web_api.py
          |
          | SimulationConfig + fichier Excel
          v
application.run_simulation_from_excel
          |
          +--> moteur / distributions / corrélations
          +--> sensibilité / convergence / percentiles
          +--> artefacts CSV / PNG existants
```

Le navigateur reçoit une représentation JSON légère : résumé statistique, table des percentiles, sensibilité, convergence, diagnostic de corrélation ainsi que des points nécessaires aux graphiques. Les milliers de tirages bruts ne sont pas envoyés au frontend.

## Choix d'ergonomie

L'interface est organisée comme un poste de décision plutôt que comme une succession de widgets :

1. configuration persistante dans un rail latéral ;
2. identité du projet et état du run immédiatement visibles ;
3. quatre indicateurs de synthèse avant les graphiques ;
4. distribution et niveaux P50/P80/P90/P95 dans une même zone de lecture ;
5. sensibilité et S-curve en second niveau ;
6. comparaison de scénarios en fin de parcours.

La comparaison fonctionne sans modifier le contrat du moteur : un run peut être « gelé » comme référence, puis un registre modifié peut être simulé. Le frontend calcule uniquement les écarts d'affichage entre résultats déjà calculés par le backend.

## Limites assumées de S5

- L'édition cellule par cellule du registre n'est pas réimplémentée dans le navigateur : Excel reste l'entrée métier de référence.
- Le mode what-if repose pour cette première version sur un registre modifié puis relancé ; une édition interactive des hypothèses pourra être ajoutée ultérieurement.
- Les exports historiques produits par le service Python restent disponibles dans le workflow existant ; le nouvel endpoint privilégie d'abord la restitution interactive.

## Lancement

Backend :

```bash
pip install -e ".[web]"
uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

Frontend :

```bash
cd web
npm install
npm run dev
```

Le serveur Vite relaie `/api` vers `127.0.0.1:8000` en développement. Après `npm run build`, FastAPI peut servir directement `web/dist`.
