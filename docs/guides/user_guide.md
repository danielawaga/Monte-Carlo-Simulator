# Guide Excel et règles d'exécution

Pour une première utilisation accompagnée, consulter le
[guide de prise en main en 30 minutes](user_guide_30min.md). Ce document décrit le schéma Excel,
les validations et les modes d'exécution du moteur.

## Commencer avec le modèle

Copier `data/templates/risk_register_template.xlsx` en dehors du dépôt avant de saisir des données
de projet. Le classeur versionné est fictif et couvre les six distributions prises en charge.

Le schéma est versionné. Ce guide décrit la version `1.0` ; une version inconnue est rejetée au lieu
d'être devinée ou modifiée silencieusement.

## Feuille `metadata`

La feuille contient les colonnes `key` et `value`.

| Clé | Obligatoire | Règle |
| --- | --- | --- |
| `schema_version` | oui | texte égal à `1.0` |
| `project_name` | oui | texte non vide |
| `analysis_type` | oui | `cost` ou `duration`, sans tenir compte de la casse |
| `default_unit` | oui | monnaie ou unité de temps commune, par exemple `MAD`, `EUR`, `jours` |
| `baseline_estimate` | non | nombre réel fini lorsqu'il est renseigné |
| `description` | non | texte non confidentiel |

`baseline_estimate` sert à comparer et à restituer les résultats. Elle n'est **pas** ajoutée
automatiquement aux échantillons. Une valeur déterministe faisant partie du total doit être saisie
comme poste actif.

## Feuille `risk_register`

Une ligne représente un poste de coût, de durée ou un risque événementiel.

| Colonne | Valeur attendue |
| --- | --- |
| `name` | nom obligatoire, non vide et unique sans tenir compte de la casse ni des espaces externes |
| `distribution` | nom canonique ou alias pris en charge |
| `minimum` | minimum pour triangulaire, PERT ou uniforme |
| `most_likely` | valeur la plus probable pour triangulaire ou PERT |
| `maximum` | maximum pour triangulaire, PERT ou uniforme |
| `mean` | moyenne arithmétique pour normale ou lognormale |
| `standard_deviation` | écart-type arithmétique pour normale ou lognormale |
| `probability` | probabilité d'un événement dans `[0, 1]` |
| `impact` | impact déterministe de l'événement |
| `lambda_shape` | forme PERT positive facultative ; vide signifie `4.0` |
| `category` | catégorie descriptive facultative |
| `unit` | unité de la ligne facultative ; vide hérite de `default_unit` |
| `enabled` | facultatif ; vide signifie actif, `FALSE` ignore la ligne |
| `notes` | texte libre facultatif |

Les colonnes `enabled` et `notes` peuvent être absentes. Toutes les autres colonnes du schéma
sont requises, même si les cellules inutilisées restent vides.

### Paramètres requis par distribution

| Distribution | Cellules requises | Domaine |
| --- | --- | --- |
| `triangular` | `minimum`, `most_likely`, `maximum` | `minimum <= most_likely <= maximum` |
| `pert` | `minimum`, `most_likely`, `maximum` | même ordre ; `lambda_shape > 0` si renseigné |
| `uniform` | `minimum`, `maximum` | `minimum <= maximum` |
| `normal` | `mean`, `standard_deviation` | `standard_deviation >= 0` |
| `lognormal` | `mean`, `standard_deviation` | moyenne arithmétique strictement positive, écart-type positif ou nul |
| `event` | `probability`, `impact` | probabilité dans `[0, 1]` |

Les cellules numériques finies et les chaînes numériques finies sont acceptées. Les booléens,
`NaN`, les infinis et le texte arbitraire ne sont pas acceptés comme paramètres numériques.

Une valeur négative est admise lorsqu'elle a un sens mathématique, par exemple l'impact négatif
d'une opportunité. Elle n'est jamais admise pour un écart-type, une forme PERT ou une moyenne
lognormale.

### Alias de distributions

Les noms canoniques sont `triangular`, `pert`, `uniform`, `normal`, `lognormal` et
`event`. Les alias suivants sont acceptés :

- `beta-pert`, `beta_pert`, `beta pert` → `pert` ;
- `log-normal`, `log_normal`, `log normal` → `lognormal` ;
- `event-based`, `event_based`, `event based`, `eventual`, `bernoulli`,
  `bernoulli-event`, `bernoulli_event` → `event`.

Les noms sont nettoyés des espaces externes et ne tiennent pas compte de la casse.

## Unités

Toutes les lignes actives doivent aboutir à une même unité. Une unité de ligne vide hérite de
`default_unit`. La comparaison ne tient pas compte de la casse, mais le moteur ne convertit ni les
monnaies ni les unités de temps. Un mélange incompatible est rejeté.

Les lignes désactivées sont ignorées avant la validation de leurs paramètres et de leur unité.

## Feuille facultative `correlations`

Cette feuille définit une matrice carrée dont les lignes et colonnes portent les noms des postes
actifs. Leur ordre peut différer : l'alignement est réalisé sur les noms.

La matrice doit :

- couvrir exactement les postes actifs ;
- être carrée, finie et symétrique ;
- contenir des coefficients dans `[-1, 1]` ;
- avoir une diagonale égale à 1 ;
- être strictement définie positive.

Le moteur utilise une copule gaussienne et une décomposition de Cholesky. Une matrice invalide est
rejetée : elle n'est ni projetée, ni tronquée, ni réparée silencieusement. Une simulation corrélée
valide produit `correlation_diagnostics.csv` avec
`automatic_repair_applied = False`.

## Utiliser l'interface

La version portable Windows est le moyen recommandé pour un consultant. Elle se lance avec
`RiskSim.exe` après décompression du ZIP ; voir le [README racine](../../README.md).

Pour développer l'interface, démarrer d'abord l'API :

```bash
pip install -e ".[web]"
uvicorn monte_carlo_simulator.web_api:app --port 8000
```

Puis, dans un second terminal :

```bash
cd web
npm install
npm run dev
```

L'interface permet l'import et l'export du registre, la construction dans le navigateur, le choix du
nombre de tirages et de la graine, les niveaux P50/P75/P80/P90/P95, les graphiques interactifs,
l'analyse de sensibilité, la convergence, les scénarios et les exports Excel ou ZIP. Les erreurs de
validation indiquent la feuille, la ligne, le poste et le champ lorsque ces informations existent.

## Utiliser la ligne de commande

```bash
python -m monte_carlo_simulator.cli \
  --input data/templates/risk_register_template.xlsx \
  --simulations 10000 \
  --seed 42 \
  --output-dir data/output
```

Sans `--input`, la démonstration fictive intégrée reste disponible :

```bash
python -m monte_carlo_simulator.cli
```

## Artefacts générés

Une exécution Excel standard produit notamment :

- `simulation_summary.csv` : moyenne, médiane, écart-type, minimum, maximum et percentiles ;
- `simulation_histogram.png` : histogramme avec marqueurs de percentiles ;
- `simulation_s_curve.png` : courbe cumulée empirique ;
- `percentile_decision_table.csv` : percentiles, dépassement, écarts et réserves ;
- `convergence_diagnostics.csv` : stabilité progressive du percentile cible ;
- `sensitivity_summary.csv` et `sensitivity_tornado.png` : influence des postes.

`baseline_comparison.csv` est ajouté lorsqu'une référence existe et
`correlation_diagnostics.csv` lorsqu'une matrice de corrélation est fournie.

## Lecture des résultats

La sensibilité de Spearman mesure le lien monotone entre les tirages d'un poste et le total simulé.
Une entrée déterministe possède une corrélation indéfinie ; elle reste documentée dans le CSV mais
est exclue du tornado par défaut. Avec des entrées corrélées, ce classement est descriptif : il ne
constitue ni une causalité ni une décomposition additive de variance.

Le diagnostic de convergence suit la stabilité du percentile cible au fil des blocs de tirages. Une
estimation stable indique que le nombre de tirages est numériquement adapté à cette simulation ; elle
ne valide pas les hypothèses métier du registre.

La comparaison à la référence rapporte la référence, la moyenne, la probabilité stricte
`P(total > référence)`, les percentiles, les écarts et une réserve non négative. L'égalité avec la
référence n'est pas considérée comme un dépassement.

## Erreurs courantes et reproductibilité

Le chargeur regroupe les erreurs indépendantes avant d'arrêter le traitement. Les causes habituelles
sont une feuille, une clé ou une colonne manquante, un nom en double, des paramètres invalides, des
unités incompatibles, un fichier non Excel ou une matrice de corrélation invalide.

Le même registre, l'ordre des postes actifs, le nombre de tirages, les niveaux de confiance et la
même graine produisent le même échantillon. Pour tracer une décision, conserver au minimum
l'identifiant du registre, le commit du dépôt, le nombre de tirages et la graine.

## Confidentialité

Les registres clients réels ne doivent jamais être commités. Les fichiers `.xlsx` et `.xls` sont
ignorés par défaut, à l’exception du modèle fictif public. Conserver les classeurs réels hors de Git
et ne partager que des données anonymisées avec l’autorisation appropriée.
