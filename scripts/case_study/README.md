# Étude de cas bâtiment

Ce dossier reproduit les trois registres synthétiques, leurs simulations, la validation fonctionnelle et le rapport PDF évolutif. Les commandes sont à exécuter depuis la racine du dépôt après l'installation du projet avec ses dépendances de développement (`pip install -e ".[dev]"`).

## 1. Construire les trois registres

```powershell
python scripts/case_study/build_variant_1.py
python scripts/case_study/build_variant_2.py
python scripts/case_study/build_variant_3.py
```

## 2. Simuler les trois variantes

```powershell
python -m monte_carlo_simulator.cli --input output/registre_risques_batiment_synthetique.xlsx --simulations 10000 --seed 42 --output-dir output/simulation_batiment
python -m monte_carlo_simulator.cli --input output/registre_risques_batiment_correlations.xlsx --simulations 10000 --seed 42 --output-dir output/simulation_batiment_correlations
python -m monte_carlo_simulator.cli --input output/registre_risques_batiment_stress.xlsx --simulations 10000 --seed 42 --output-dir output/simulation_batiment_stress
```

Chaque dossier contient huit livrables : résumé, histogramme, courbe en S, table de décision, convergence, sensibilité, tornado et comparaison à la baseline.

## 3. Exécuter la validation fonctionnelle

```powershell
python scripts/case_study/validate_functional.py
```

Le résultat attendu est `44/44` contrôles réussis. Les sorties détaillées sont écrites sous `output/functional_validation/`. Les preuves destinées à Git doivent ensuite être synchronisées sous `docs/validation/`.

## 4. Reconstruire le rapport PDF

```powershell
python scripts/case_study/generate_report.py
python scripts/case_study/integrate_variant_2_report.py
python scripts/case_study/integrate_variant_3_report.py
python scripts/case_study/integrate_validation_report.py
```

L'ordre est obligatoire : le rapport initial produit la variante 1, puis chaque intégrateur remplace les chapitres finaux provisoires par la mise à jour suivante. Le résultat final est `reports/case_study/etude_cas_batiment_monte_carlo.pdf`.

## 5. Vérifications du dépôt

```powershell
ruff check .
ruff format --check .
pytest --cov=monte_carlo_simulator --cov-report=term-missing --cov-fail-under=85
mypy src/monte_carlo_simulator
```

Les classeurs Excel et les sorties brutes restent hors Git conformément au `.gitignore`. Ils contiennent uniquement des données synthétiques, mais leur exclusion conserve la même politique que pour de futurs registres confidentiels.