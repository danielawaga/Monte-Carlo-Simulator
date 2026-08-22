# Méthodologie technique

Pour une version destinée à un public non mathématicien, voir [`methodology_note.md`](methodology_note.md). Ce document décrit les choix techniques et invariants du moteur.

## 1. Simulation Monte Carlo et reproductibilité

Le moteur construit un seul `numpy.random.Generator` à partir de `random_seed`, puis le transmet aux distributions. À registre, ordre des postes, configuration et seed identiques, les mêmes vecteurs sont reproduits.

Chaque poste est simulé sous forme d'un vecteur NumPy complet. Les vecteurs sont additionnés élément par élément pour produire la distribution du total. Aucune boucle Python ne porte sur les tirages individuels ; la boucle métier porte sur les postes.

La taille de simulation doit être un entier strictement positif.

## 2. Validation numérique générale

Dans l'API Python, les paramètres requis doivent être des nombres réels finis. Les booléens, chaînes arbitraires, nombres complexes, `NaN` et infinis sont refusés.

À la frontière Excel, une chaîne numérique finie peut être convertie explicitement. Les cellules vides, `NaN` et chaînes composées uniquement d'espaces sont considérées comme absentes.

## 3. Distributions

### Triangulaire

Paramètres : minimum `a`, mode `m`, maximum `b`, avec `a <= m <= b`.

```text
E[X] = (a + m + b) / 3
```

Les valeurs négatives sont admises. Si `a = m = b`, le résultat est déterministe. L'implémentation utilise une transformation inverse stable afin d'éviter les débordements associés à des bornes finies très éloignées.

### Beta-PERT

Paramètres : `a`, `m`, `b` et `lambda_shape = λ > 0`, avec `λ = 4` par défaut.

Pour `a < b` :

```text
alpha = 1 + λ × (m - a) / (b - a)
beta  = 1 + λ × (b - m) / (b - a)
X     = a + (b - a) × Y,  Y ~ Beta(alpha, beta)
```

Son espérance est :

```text
E[X] = (a + λ × m + b) / (λ + 2)
```

Si `a = m = b`, le résultat est constant.

### Uniforme

Deux bornes finies `a <= b` :

```text
E[X] = (a + b) / 2
```

Les bornes négatives sont valides. `a = b` produit une série constante.

### Normale

Paramètres : moyenne arithmétique finie `m` et écart-type `s >= 0`. La loi n'est pas bornée et peut produire des valeurs négatives. `s = 0` produit une série constante.

### Log-normale

Les paramètres Excel sont une moyenne arithmétique `m > 0` et un écart-type arithmétique `s >= 0`. Pour `s > 0`, ils sont transformés vers l'espace logarithmique :

```text
sigma_log² = ln(1 + (s / m)²)
mu_log     = ln(m) - sigma_log² / 2
```

Les tirages sont strictement positifs. `s = 0` produit une série constante égale à `m`.

### Risque événementiel

Avec une probabilité `p` et un impact `I` :

```text
X = I avec probabilité p
X = 0 avec probabilité 1 - p
E[X] = p × I
Var[X] = p × (1 - p) × I²
```

Un impact négatif peut représenter une opportunité. `p = 0`, `p = 1` et `I = 0` sont traités comme cas déterministes.

## 4. Noms et alias

Noms canoniques : `triangular`, `pert`, `uniform`, `normal`, `lognormal`, `event`.

Alias pris en charge :

- `beta-pert`, `beta_pert`, `beta pert` → `pert` ;
- `log-normal`, `log_normal`, `log normal` → `lognormal` ;
- `event-based`, `event_based`, `event based`, `eventual`, `bernoulli`, `bernoulli-event`, `bernoulli_event` → `event`.

La casse et les espaces externes sont ignorés. Les noms de postes doivent rester uniques après nettoyage, sans tenir compte de la casse.

## 5. Registre Excel et unités

Le schéma `1.0` constitue une frontière d'entrée versionnée. Une ligne active validée devient un `RiskItem`. Les lignes désactivées sont ignorées avant la validation de leurs paramètres.

Toutes les unités actives doivent correspondre à `default_unit` sans tenir compte de la casse. Le moteur n'effectue aucune conversion de devise ou d'unité de temps.

`baseline_estimate` est une référence optionnelle. Elle n'entre jamais dans l'agrégation du total. Un montant déterministe appartenant réellement au total doit être représenté par un poste explicite.

## 6. Corrélations et copule gaussienne

La feuille `correlations` optionnelle définit la dépendance entre les postes actifs. Les lignes et colonnes sont alignées par nom avant construction de `CorrelationMatrix`.

La matrice doit être :

- carrée ;
- finie ;
- symétrique ;
- bornée dans `[-1, 1]` ;
- de diagonale unitaire ;
- strictement définie positive.

La simulation corrélée utilise une copule gaussienne : normales multivariées corrélées via Cholesky, transformation vers des probabilités uniformes, puis fonctions quantiles des distributions marginales.

La politique est **strict-no-repair**. Une matrice invalide est rejetée avec diagnostic ; aucune projection, troncature ou perturbation silencieuse n'est appliquée. Un run corrélé valide produit `correlation_diagnostics.csv` et indique `automatic_repair_applied = False`.

## 7. Percentiles et Value at Risk

Pour un niveau `q` strictement compris entre 0 et 1, le percentile est le quantile empirique du total.

Les libellés conservent les décimales significatives :

- `0.50` → `P50` ;
- `0.951` → `P95.1` ;
- `0.995` → `P99.5`.

Les niveaux dupliqués sont rejetés. Dans ce projet, la VaR au niveau `q` correspond directement au quantile `q` de la distribution du total ; elle ne représente pas automatiquement un écart à la baseline.

## 8. Baseline, dépassement et réserve

Lorsqu'une baseline finie est fournie :

```text
exceedance_probability = mean(total > baseline)
gap(Px)                = Px - baseline
reserve(Px)            = max(gap(Px), 0)
```

L'égalité avec la baseline n'est pas comptée comme dépassement. Les écarts relatifs ne sont définis que pour une baseline strictement positive.

## 9. S-curve

La S-curve est la fonction de répartition empirique du total. Après tri croissant des échantillons, chaque valeur est associée à sa probabilité cumulée empirique.

Elle permet de lire :

- `P(total <= budget)` pour un budget donné ;
- le budget correspondant à un niveau de confiance donné.

Le workflow exporte une version statique, tandis que l'interface React construit une version interactive à partir des mêmes échantillons.

## 10. Sensibilité de Spearman

Pour chaque poste, le moteur calcule la corrélation de rang de Spearman entre les tirages du poste et le total simulé.

Spearman est choisi parce qu'il mesure une association monotone sans supposer de relation linéaire ou de marges normales. Il convient aux distributions asymétriques et aux événements contenant des ex æquo.

Les postes déterministes sont constants ; leur coefficient est mathématiquement indéfini. Ils sont signalés avec `undefined_reason = constant_input` plutôt que forcés à zéro.

Les postes définis sont classés par `abs(rho)`. Le signe conserve la direction de l'association.

Avec des entrées corrélées :

- `rho` reste descriptif ;
- il ne mesure pas une causalité ;
- il ne constitue pas une décomposition additive de variance ;
- ses valeurs absolues ne doivent pas être normalisées pour sommer à 100 %.

## 11. Convergence automatique

Le diagnostic de convergence suit un percentile cible sur des blocs cumulés d'échantillons.

Pour chaque bloc, il calcule :

- le nombre cumulé de tirages ;
- l'estimation du percentile ;
- la variation absolue ;
- la variation relative par rapport aux deux estimations successives ;
- si la variation respecte la tolérance ;
- le nombre de blocs stables consécutifs ;
- un unique indicateur `stop_recommended` lorsque les critères sont atteints.

Le service choisit un `block_size` au plus égal à 1 000 et suit le plus haut niveau de confiance configuré.

La convergence mesure la stabilité numérique de l'estimateur. Elle ne valide ni la distribution choisie, ni les bornes, ni les corrélations.

## 12. Restitution et interface

Le cœur métier est indépendant de l'interface. Celle-ci appelle l'API HTTP, qui délègue à `run_simulation_from_excel`, puis transforme les échantillons et artefacts en vues interactives.

Cette séparation garantit que la CLI et l'interface utilisent le même moteur et les mêmes règles de validation.

Le niveau de décision affiché dans l'interface peut être P50, P80, P90 ou P95. Les cartes de décision recalculent directement le quantile, la probabilité de dépassement et la réserve à partir des échantillons du run.

## 13. Validation métier

Les tests automatisés vérifient les invariants logiciels et numériques. La crédibilité des hypothèses nécessite une validation terrain séparée.

Le protocole `docs/consultant_validation_workshop.md` demande notamment de documenter :

- les paramètres contestés ;
- la justification des corrélations non nulles ;
- la baseline retenue ;
- le niveau de confiance utile ;
- la cohérence du tornado avec l'expérience métier ;
- les actions, responsables et échéances.

Le cas synthétique du dépôt valide le chemin logiciel mais ne remplace pas cette validation métier.

## 14. Fonctionnalités hors périmètre S4

Les extensions prévues après la semaine 4 sont principalement :

- mode what-if interactif ;
- comparaison de scénarios ;
- exports PDF ou PowerPoint décisionnels ;
- calibration empirique sur historique autorisé ;
- éventuelle modélisation conjointe coût × délai.
