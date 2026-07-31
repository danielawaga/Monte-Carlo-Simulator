# Etude de cas batiment

Ces scripts reproduisent les trois registres synthetiques, leurs simulations, la validation fonctionnelle et le rapport PDF evolutif.

Ordre d'execution depuis la racine du depot :

1. `python scripts/case_study/build_variant_1.py`
2. `python scripts/case_study/build_variant_2.py`
3. `python scripts/case_study/build_variant_3.py`
4. Executer la CLI sur chaque classeur avec 10 000 simulations et la graine 42.
5. `python scripts/case_study/validate_functional.py`
6. `python scripts/case_study/generate_report.py`
7. `python scripts/case_study/integrate_variant_3_report.py`
8. `python scripts/case_study/integrate_validation_report.py`

Les classeurs et sorties restent sous `output/`. Les fichiers Excel ne sont pas versions, conformement a la politique de confidentialite du depot. Les preuves tabulaires publiees se trouvent dans `docs/validation/`.