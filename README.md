# RiskSim — Monte Carlo Simulator

RiskSim est une application locale d'analyse probabiliste des risques de **coût** et de **durée**
des projets. À partir d'un registre de risques Excel ou créé dans l'interface, elle exécute une
simulation Monte-Carlo, calcule des indicateurs de décision et produit des exports exploitables.

Le navigateur affiche l'interface tandis que le moteur Python calcule localement. Les données ne
sont pas transmises sur le réseau.

## Fonctionnalités

- création ou import d'un registre de risques Excel ;
- distributions triangulaire, PERT, uniforme, normale, lognormale et événementielle ;
- corrélations optionnelles entre postes par copule gaussienne ;
- simulations vectorisées et reproductibles grâce à la graine aléatoire ;
- P50, P75, P80, P90, P95, dépassement de référence et réserve ;
- histogramme, S-curve, sensibilité de Spearman et diagnostic de convergence ;
- sauvegarde locale des registres, scénarios et simulations ;
- export Excel et dossier ZIP des artefacts de résultats.

## Version portable Windows

La version prête à l'emploi est disponible dans
[`output/packages/RiskSim-Windows-x64-Portable.zip`](output/packages/RiskSim-Windows-x64-Portable.zip).
Elle embarque Python, l'API locale, l'interface React et ses dépendances : aucune installation
préalable de Python, Node.js ou package n'est requise.

1. Depuis GitHub, télécharger le fichier ZIP à l’aide du bouton de téléchargement du fichier.
2. Décompresser entièrement l'archive dans un dossier local.
3. Ouvrir `RiskSim-Portable` et lancer `RiskSim.exe`.
4. Laisser le terminal ouvert : il indique le démarrage et les éventuelles erreurs.
5. Le navigateur s'ouvre automatiquement lorsque l'application est prête.

Pour arrêter l'application, utiliser `Ctrl+C`, saisir `exit`, `quit` ou `q` dans le terminal, ou
cliquer sur « Quitter RiskSim » dans l'interface. Attendre le message de fin avant de déplacer ou
supprimer le dossier.

L'archive est stockée avec Git LFS. Pour la récupérer au moyen d'un clone local, installer Git LFS
puis exécuter :

```bash
git clone --branch portable-risksim-windows https://github.com/danielawaga/Monte-Carlo-Simulator.git
cd Monte-Carlo-Simulator
git lfs pull
```

Sans Git LFS, Git ne récupère qu'un fichier de référence au lieu de l'archive complète.

## Développement local

### Préparer Python

Python 3.11 ou plus récent est requis.

```bash
python -m venv .venv
# PowerShell : .venv\Scripts\Activate.ps1
# Git Bash/Linux/macOS : source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,web,packaging]"
```

### Lancer l'interface React

Dans un premier terminal, démarrer l'API :

```bash
python -m uvicorn monte_carlo_simulator.web_api:app --reload --port 8000
```

Dans un second terminal :

```bash
cd web
npm install
npm run dev
```

Ouvrir ensuite l'adresse indiquée par Vite, généralement `http://localhost:5173`.

### Construire l'interface locale

```bash
cd web
npm run build
cd ..
python -m monte_carlo_simulator.launcher
```

Le lanceur sert l'interface construite depuis `127.0.0.1` et ouvre le navigateur lorsque l'API
répond. L'adresse d'écoute est volontairement limitée à la machine locale.

## Parcours utilisateur

1. Dans **Registre de risques**, créer un projet ou importer un fichier Excel.
2. Renseigner les postes, leurs distributions et, si nécessaire, la matrice de corrélation.
3. Contrôler le registre dans l'étape **Validation**.
4. Dans **Simulation**, choisir le nombre de tirages, la graine, les niveaux de confiance et le
   niveau de décision.
5. Lancer le calcul, puis consulter les onglets **Synthèse**, **Distribution**, **Sensibilité** et
   **Robustesse** des résultats.
6. Exporter le classeur de résultats ou le dossier ZIP des graphiques et tableaux.

La valeur de référence est une donnée de comparaison : elle n'est jamais ajoutée automatiquement au
total simulé. Une même combinaison de registre, paramètres et graine produit le même échantillon.

## Architecture

| Couche | Emplacement | Responsabilité |
| --- | --- | --- |
| Interface | `web/` | React, TypeScript et Vite ; saisie, affichage et navigation. |
| API | `src/monte_carlo_simulator/web_api.py` | API FastAPI et distribution de l'interface construite. |
| Moteur | `src/monte_carlo_simulator/` | distributions, corrélations, statistiques et exports. |
| Données | SQLite locale | projets, registres, scénarios et simulations conservées. |
| Packaging | `packaging/` | construction PyInstaller de la version portable Windows. |

React ne contient pas les règles probabilistes : il appelle l'API, qui délègue au moteur Python. La
description détaillée est disponible dans [l'architecture technique](docs/reference/architecture.md).

## Contrat Excel

Le modèle public se trouve dans
[`data/templates/risk_register_template.xlsx`](data/templates/risk_register_template.xlsx). Il
utilise le schéma versionné `1.0` :

- feuille `metadata` : identité du projet, type d'analyse, unité commune et référence facultative ;
- feuille `risk_register` : postes, distributions et paramètres ;
- feuille `correlations` : facultative, uniquement en cas de dépendances entre postes.

Le détail des colonnes, règles de validation et artefacts est décrit dans le
[guide Excel](docs/guides/user_guide.md).

## Tests et qualité

```bash
# Python
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest -q

# Interface React
cd web
npm test -- --pool=threads
npm run build
```

L'intégration continue teste Python 3.11 et 3.12, le lint, le formatage, le typage, la couverture,
les tests React et la construction de l'interface. La version portable a en outre été validée par un
démarrage réel, une simulation, un export et une fermeture depuis un dossier ZIP nouvellement extrait.

## Organisation du dépôt

```text
src/monte_carlo_simulator/  moteur Python, API et persistance
web/                        interface React
data/templates/             modèle Excel public
packaging/                  configuration PyInstaller et notice portable
tests/                       tests unitaires et d'intégration
docs/                        guides, références, archives et résultats de validation
scripts/                    génération de jeux d'essai et rapports
reports/                    livrables de stage et preuves datées
```

## Documentation

Le point d'entrée complet est [docs/README.md](docs/README.md).

- [Guide de prise en main en 30 minutes](docs/guides/user_guide_30min.md)
- [Guide Excel et règles d'exécution](docs/guides/user_guide.md)
- [Passation technique](docs/guides/handover.md)
- [Vue d'ensemble du projet](docs/reference/project_overview.md)
- [Architecture technique](docs/reference/architecture.md)
- [Note méthodologique vulgarisée](docs/reference/methodology_note.md)
- [Méthodologie technique](docs/reference/methodology.md)

## Confidentialité et limites

Ne jamais ajouter de registres réels, d'exports clients ou de bases SQLite au dépôt. Les fichiers
Excel réels doivent rester hors de Git et être anonymisés avant tout partage autorisé.

RiskSim vérifie la cohérence mathématique et informatique des hypothèses ; il ne garantit pas que
ces hypothèses décrivent fidèlement un projet réel. Cette validation métier relève du consultant et
des responsables du projet.
