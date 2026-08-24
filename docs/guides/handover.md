# Passation technique — Monte Carlo Simulator

Ce document sert de support à la session de reprise prévue en semaine 4. Il doit être parcouru avec le repreneur interne sur une machine propre, en exécutant réellement le flux Excel → simulation → export.

## 1. Repreneur

- **Nom / rôle :** à renseigner par le maître de stage
- **Date de passation :** à renseigner
- **Version transmise :** branche ou commit de release à renseigner
- **Dépôt :** `Rudolf-Staline/Monte-Carlo-Simulator`

L'identification du repreneur est une décision organisationnelle externe au dépôt. La passation n'est considérée comme terminée qu'après exécution de la checklist de validation en fin de document.

## 2. Architecture à connaître

```text
src/monte_carlo_simulator/
  models/          objets métier et configuration
  distributions/   tirages des six distributions
  engine/          agrégation et dépendances Monte Carlo
  analysis/        percentiles, baseline, convergence, sensibilité
  io/              import Excel et exports CSV
  visualization/   graphiques statiques exportés
  application/     orchestration des workflows
web/                interface React + TypeScript (seule interface)
  storage/          base SQLite locale : registres enregistrés et historique
scripts/            génération de cas et validation reproductible
tests/              tests unitaires et d'intégration
data/templates/     modèles publics et fictifs
docs/               guides/, reference/, validation/ et archive/
reports/            livrables générés (rapport S5, étude de cas)
```

Le principe important est que l'interface ne contient pas le moteur métier. Elle appelle l'API HTTP (`web_api.py`), qui délègue à `run_simulation_from_excel` — le même workflow que la CLI.

## 3. Installation de reprise

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell
python -m pip install --upgrade pip
pip install -e ".[dev,web]"
```

Vérifications :

```bash
ruff check .
ruff format --check .
pytest -v
pytest --cov=monte_carlo_simulator --cov-report=term-missing --cov-fail-under=85
mypy src/monte_carlo_simulator
```

## 4. Exécuter les trois chemins importants

### Interface consultant

Deux terminaux. D'abord l'API Python :

```bash
pip install -e ".[web]"
uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

Puis l'interface :

```bash
cd web
npm install
npm run dev
```

Ouvrir l'adresse affichée par Vite, aller dans « Registre de risques », importer
`data/templates/risk_register_template.xlsx`, lancer 10 000 tirages, changer P80/P90 et télécharger
le dossier ZIP d'artefacts depuis l'écran Résultats.

### CLI

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

### Cas S3 reproductible

```bash
python -m scripts.run_s3_acceptance_case
```

Ce dernier valide le chemin logiciel corrélé sur des données synthétiques ; il ne constitue pas une validation métier.

## 5. Invariants qu'il ne faut pas casser

1. La baseline est une référence ; elle n'est jamais ajoutée implicitement au total simulé.
2. Toutes les lignes actives d'un registre utilisent une unité cohérente.
3. Les matrices de corrélation invalides sont rejetées ; aucune réparation silencieuse n'est appliquée.
4. Une seed identique avec le même registre et la même configuration doit reproduire les tirages.
5. Les postes déterministes restent visibles dans les données de sensibilité mais sont marqués comme Spearman indéfini.
6. Les données réelles confidentielles ne sont pas commitées dans le dépôt.
7. L'interface ne doit pas réimplémenter la logique probabiliste déjà présente dans `src/`.

## 6. Artefacts attendus

Un run standard produit :

- résumé statistique ;
- histogramme ;
- S-curve ;
- table de percentiles ;
- diagnostic de convergence ;
- sensibilité Spearman ;
- tornado.

Un run avec baseline ajoute la comparaison et les réserves. Un run avec corrélations ajoute le diagnostic de matrice.

## 7. Où modifier quoi ?

- Nouvelle distribution : `distributions/`, modèle/validation associé et tests.
- Nouveau contrôle de registre : `io/` et tests de validation Excel.
- Nouvel indicateur analytique : `analysis/`, export éventuel puis branchement dans `application/service.py`.
- Nouveau graphique statique : `visualization/`.
- Nouvelle restitution interactive sans nouvelle logique métier : `web/src/`.
- Nouveau workflow complet : `application/`.

## 8. Diagnostic rapide en cas de problème

### Le classeur est refusé

Lire toutes les erreurs agrégées avant de modifier le fichier. Les plus fréquentes sont : colonne manquante, paramètre vide, distribution inconnue, unité incohérente ou matrice de corrélation invalide.

### La simulation fonctionne mais l'interface casse

Tester d'abord la CLI avec le même fichier. Si la CLI fonctionne, isoler le problème dans l'API HTTP puis dans la couche React. Si la CLI échoue aussi, remonter vers le service puis le loader ou le moteur.

### Le résultat semble faux mais les tests passent

Les tests valident surtout le comportement logiciel. Revenir aux hypothèses métier : bornes, unités, baseline, dépendances, double comptage et interprétation des événements.

## 9. Checklist de passation

La session est considérée comme terminée lorsque le repreneur a lui-même :

- [ ] cloné ou récupéré le dépôt ;
- [ ] créé l'environnement et installé `.[dev,web]` ;
- [ ] exécuté la suite de tests ;
- [ ] lancé l'API puis l'interface React ;
- [ ] chargé le modèle Excel ;
- [ ] produit un run à 10 000 tirages ;
- [ ] expliqué P50, P80, P90 et la probabilité de dépassement ;
- [ ] expliqué pourquoi la baseline n'est pas additionnée ;
- [ ] retrouvé le top 3 du tornado ;
- [ ] identifié le point de convergence ou expliqué son absence ;
- [ ] téléchargé le ZIP d'artefacts ;
- [ ] localisé les modules à modifier pour une extension ;
- [ ] confirmé les règles de confidentialité.

## 10. Extensions prévues après S4

Les semaines 5–6 peuvent absorber les retours utilisateurs puis développer, selon priorité : mode what-if, comparaison de scénarios, exports PDF/PowerPoint et calibration sur historique autorisé.
