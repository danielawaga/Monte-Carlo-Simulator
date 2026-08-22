# Architecture

Le projet conserve sept couches explicites : `models`, `distributions`, `engine`, `analysis`,
`io`, `visualization` et `application`.

## Responsabilités

1. **`models`**
   - porte `RiskItem`, `SimulationConfig`, `SimulationResult` ;
   - porte `RiskRegisterMetadata`, `RiskRegister` et `ExcelSimulationRun` ;
   - ne lit pas Excel et ne génère aucun tirage.

2. **`distributions`**
   - valide et encapsule les six lois probabilistes ;
   - utilise un registre de fabriques, sans chaîne centrale de `if/elif` dans le moteur ;
   - produit un vecteur NumPy complet par appel.

3. **`engine`**
   - crée un seul `numpy.random.Generator` à partir de la graine ;
   - demande un vecteur à chaque distribution puis agrège les colonnes ;
   - ne boucle jamais sur les tirages individuels.

4. **`analysis`**
   - calcule les moments et quantiles ;
   - forme des noms de percentiles sans troncature ni collision silencieuse.

5. **`io`**
   - définit le contrat Excel versionné dans `schema.py` ;
   - génère le modèle public avec `excel_template.py` ;
   - extrait les cellules avec leur ligne Excel dans `excel_reader.py` ;
   - convertit et valide les données dans `validators.py` ;
   - exporte le résumé CSV.

6. **`visualization`**
   - sauvegarde l'histogramme et ses repères de percentiles ;
   - ne décide pas des paramètres du modèle.

7. **`application`**
   - orchestre lecture, validation, simulation et artefacts ;
   - conserve séparément le workflow de démonstration historique ;
   - fournit le service appelé par la CLI.

## Flux Excel

```text
workbook .xlsx
  -> extraction metadata + risk_register + correlations optionnelles + lignes source
  -> validation agrégée (RiskRegisterValidationError)
  -> RiskRegisterMetadata + list[RiskItem] + CorrelationMatrix optionnelle
  -> MonteCarloSimulator ou GaussianCopulaSampler
  -> SimulationResult
  -> CSV + histogramme + ExcelSimulationRun
```

L'API principale `load_risk_register` retourne un objet structuré et non un simple DataFrame.
`load_risk_register_excel` reste un adaptateur de compatibilité pour obtenir les lignes du schéma,
mais le service applicatif ne l'utilise pas.

Les erreurs attendues de fichier ou de données sont traduites en `RiskRegisterIssue`. Elles sont
agrégées avec feuille, ligne, poste, champ et valeur. Aucun `try/except` global ne transforme les
erreurs de programmation en messages métier.

## Frontières actuelles

La CLI est opérationnelle. L'interface React de `web/` était alors hors périmètre. Les modules de convergence, sensibilité, courbe en S et tornade restent hors périmètre. Les corrélations par copule gaussienne sont implémentées pour les classeurs Excel qui fournissent une matrice strictement définie positive.

## Sensitivity and tornado V1

`analysis/sensitivity.py` owns the Spearman computation and tornado-data preparation.
`visualization/tornado.py` only renders Matplotlib figures. `application/service.py`
orchestrates the Excel workflow after simulation by reusing `SimulationResult.item_samples`
and `SimulationResult.samples`; the engine remains limited to sample generation and total
aggregation.

Excel runs now persist `sensitivity_summary.csv` and `sensitivity_tornado.png` in addition
to the historical summary CSV and histogram PNG. `ExcelSimulationRun` exposes the new
`sensitivity_path` and `tornado_path` fields while keeping `histogram_path`, `summary_path`
and `source_path` unchanged.
