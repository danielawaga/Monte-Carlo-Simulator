# Guide utilisateur — prise en main en 30 minutes

Ce guide vise un consultant qui veut exécuter une simulation sans écrire de code. Le flux normal est : **registre Excel → contrôles → simulation → lecture décisionnelle → export**.

## 0–5 min — installer l'application

Prérequis : Python 3.11 ou plus récent et Git.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[ui]"
streamlit run streamlit_app/app.py
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[ui]"
streamlit run streamlit_app/app.py
```

Le navigateur ouvre l'interface. Si ce n'est pas le cas, utiliser l'adresse locale affichée par Streamlit dans le terminal.

## 5–10 min — partir du bon fichier Excel

Utiliser `data/templates/risk_register_template.xlsx`, également téléchargeable depuis la barre latérale de l'application.

Le classeur suit le schéma `1.0` et contient au minimum :

- `metadata` : nom du projet, type d'analyse, unité, baseline facultative ;
- `risk_register` : postes et paramètres de distributions ;
- `instructions` : rappel du format ;
- `correlations` : facultatif, uniquement si des dépendances doivent être modélisées.

Ne jamais modifier arbitrairement les noms des colonnes du schéma. Pour un vrai cas client, travailler sur une copie hors du dépôt et anonymiser les informations sensibles.

## 10–15 min — renseigner les hypothèses

Chaque ligne active du registre représente un poste de coût, de délai ou un risque événementiel. Les six distributions disponibles sont :

| Distribution | Paramètres principaux | Usage typique |
| --- | --- | --- |
| `triangular` | minimum, plus probable, maximum | estimation expert simple |
| `pert` | minimum, plus probable, maximum | estimation expert plus concentrée autour du mode |
| `uniform` | minimum, maximum | aucune valeur plus probable qu'une autre |
| `normal` | moyenne, écart-type | incertitude symétrique non bornée |
| `lognormal` | moyenne arithmétique, écart-type | valeurs positives et asymétriques |
| `event` | probabilité, impact | risque discret qui arrive ou non |

Toutes les lignes actives doivent utiliser la même unité que `default_unit`. La baseline est une **référence de comparaison** : elle n'est jamais ajoutée automatiquement au total simulé.

Si une feuille `correlations` est utilisée, la matrice doit être carrée, symétrique, avoir une diagonale égale à 1 et être strictement définie positive. Le moteur refuse une matrice invalide ; il ne la répare pas silencieusement.

## 15–20 min — lancer la simulation

Dans la barre latérale :

1. charger le fichier `.xlsx` ;
2. choisir le nombre de tirages — `10 000` est le point de départ prévu par le projet ;
3. conserver la seed `42` pour un run reproductible, ou choisir une autre seed ;
4. choisir le niveau de décision `P50`, `P80`, `P90` ou `P95` ;
5. cliquer sur **Lancer la simulation**.

En cas d'erreur de registre, l'interface affiche les problèmes avec la feuille, la ligne, le poste et le champ concernés quand ces informations sont disponibles.

## 20–25 min — lire les résultats

### Les quatre indicateurs en tête

- **Px** : valeur sous laquelle tombent `x %` des tirages ;
- **moyenne simulée** : moyenne de la distribution obtenue ;
- **P(dépassement baseline)** : fréquence empirique stricte `P(total > baseline)` ;
- **réserve jusqu'à Px** : `max(Px - baseline, 0)`.

Exemple d'interprétation : si `P90 = 12,4 M MAD`, un budget de `12,4 M MAD` n'est dépassé que dans environ 10 % des tirages du modèle. Cela ne signifie pas que la vraie probabilité de dépassement est garantie à 10 % : la qualité du résultat dépend des hypothèses saisies.

### Onglet Décision

- histogramme interactif de la distribution ;
- S-curve, c'est-à-dire la probabilité cumulée de ne pas dépasser chaque valeur ;
- table de percentiles ;
- comparaison à la baseline quand elle existe.

### Onglet Sensibilité

Le tornado classe les postes selon la corrélation de rang de Spearman entre leurs tirages et le total. Une forte valeur absolue signale un poste à examiner en priorité. Avec des entrées corrélées, ce classement reste descriptif : ce n'est ni une causalité ni un partage additif de la variance.

### Onglet Convergence

Le graphique suit la stabilité du percentile cible au fur et à mesure que le nombre de tirages augmente. Le critère automatique peut signaler un nombre de tirages à partir duquel les variations deviennent suffisamment faibles. Une convergence numérique correcte ne valide pas les hypothèses métier.

## 25–30 min — exporter et tracer la décision

L'onglet **Exports** permet de télécharger chaque artefact ou un ZIP complet. Selon le contenu du registre, le pack peut inclure :

- `simulation_summary.csv` ;
- `simulation_histogram.png` ;
- `simulation_s_curve.png` ;
- `percentile_decision_table.csv` ;
- `convergence_diagnostics.csv` ;
- `sensitivity_summary.csv` ;
- `sensitivity_tornado.png` ;
- `baseline_comparison.csv` si une baseline existe ;
- `correlation_diagnostics.csv` si une matrice de corrélation existe.

Pour une restitution, conserver au minimum le registre source autorisé, la seed, le nombre de tirages, la version ou le commit du moteur et les artefacts de décision utilisés.

## Problèmes fréquents

### « Risk register validation failed »

Corriger toutes les erreurs listées avant de relancer. Le loader agrège les problèmes indépendants afin d'éviter une boucle correction → relance → nouvelle erreur.

### La probabilité de dépassement n'apparaît pas

Le champ `baseline_estimate` de la feuille `metadata` est vide. Les percentiles restent valides mais aucune comparaison à une référence ne peut être calculée.

### La matrice de corrélation est refusée

Vérifier les noms de postes, la symétrie, la diagonale et les coefficients. Une matrice peut sembler raisonnable ligne par ligne tout en n'étant pas strictement définie positive.

### Le tornado contient moins de postes que le registre

Un poste déterministe produit une colonne constante ; Spearman est alors mathématiquement indéfini. Le poste reste présent dans le CSV avec une raison explicite mais il est exclu du graphique par défaut.

## Alternative en ligne de commande

Le même cœur applicatif peut être utilisé sans interface :

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

L'interface Streamlit et la CLI appellent le même moteur ; elles diffèrent surtout par la restitution et l'interaction utilisateur.
