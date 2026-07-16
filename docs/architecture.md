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
  -> extraction metadata + risk_register + lignes source
  -> validation agrégée (RiskRegisterValidationError)
  -> RiskRegisterMetadata + list[RiskItem]
  -> MonteCarloSimulator
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

La CLI est opérationnelle. `streamlit_app` reste un squelette. Les modules réservés aux
corrélations, convergence, sensibilité, courbe en S et tornade ne constituent pas des
fonctionnalités implémentées.
