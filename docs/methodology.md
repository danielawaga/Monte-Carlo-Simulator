# Méthodologie

## Simulation Monte Carlo

La simulation Monte Carlo répète un grand nombre de tirages aléatoires pour approximer la
distribution d'un résultat global. Le moteur construit un seul `numpy.random.Generator` à partir
de `random_seed`, puis le transmet à chaque loi. Deux simulations ayant la même configuration,
les mêmes postes dans le même ordre et la même graine produisent exactement les mêmes vecteurs.
La taille demandée doit être un entier strictement positif.

## Lois prises en charge

Dans l'API Python, tous les paramètres requis doivent être des nombres réels finis : les booléens,
chaînes, nombres complexes, `NaN` et infinis sont refusés. À la frontière Excel, une chaîne
numérique finie est convertie explicitement ; les chaînes arbitraires, booléens et valeurs non
finies sont refusés. Les cellules vides, les valeurs `NaN` et les chaînes composées uniquement
d'espaces sont considérées comme absentes.

### Triangulaire

La loi triangulaire est définie par un minimum `a`, une valeur la plus probable `m` et un maximum
`b`, avec `a ≤ m ≤ b`. Son espérance vaut `(a + m + b) / 3`. Les valeurs négatives sont admises.
Si `a = m = b`, le résultat est le vecteur constant `a`. Les modes placés sur l'une des deux
bornes sont également valides. Le tirage utilise l'inverse de la fonction de répartition sur
l'intervalle unité, puis une interpolation stable, afin que des bornes finies extrêmes ne
produisent pas d'infinis par débordement de `b - a`.

### Beta-PERT

La loi Beta-PERT utilise les mêmes trois valeurs et un paramètre de forme `lambda_shape = λ`,
strictement positif et égal à `4.0` par défaut. Pour `a < b`, une variable bêta `Y` est définie par :

```text
alpha = 1 + λ × (m - a) / (b - a)
beta  = 1 + λ × (b - m) / (b - a)
X     = a + (b - a) × Y
```

L'implémentation évalue les proportions et l'interpolation sous une forme numériquement stable
pour éviter le débordement lorsque les bornes finies sont très éloignées. Le mode transformé vaut
`m` et l'espérance vaut :

```text
E[X] = (a + λ × m + b) / (λ + 2)
```

Si `a = m = b`, le résultat est constant et aucun paramètre bêta n'est calculé.

### Uniforme

La loi uniforme accepte deux bornes finies `a ≤ b`. Toutes les valeurs de l'intervalle ont la même
densité et l'espérance vaut `(a + b) / 2`. Les bornes négatives sont valides. Si `a = b`, le
résultat est le vecteur constant `a`.

### Normale

La loi normale est paramétrée par une moyenne arithmétique finie `m` et un écart-type fini `s ≥ 0`.
Elle n'est pas bornée : une moyenne négative est mathématiquement valide et des tirages négatifs
restent possibles quelle que soit une moyenne positive. Si `s = 0`, le résultat est le vecteur
constant `m`.

### Log-normale

Les champs `mean = m` et `standard_deviation = s` sont exprimés dans l'espace arithmétique, avec
`m > 0` et `s ≥ 0`. Pour `s > 0`, le moteur les convertit en paramètres de l'espace logarithmique :

```text
sigma_log² = ln(1 + (s / m)²)
mu_log     = ln(m) - sigma_log² / 2
```

La conversion est calculée sous une forme logarithmique stable afin d'éviter le débordement du
rapport `s / m`, tout en appliquant exactement ces formules. Les tirages sont strictement positifs.
Si `s = 0`, le résultat est le vecteur constant positif `m`.

### Risque événementiel

Un risque événementiel associe une probabilité finie `p ∈ [0, 1]` à un impact fini `I` :

```text
X = I avec la probabilité p
X = 0 avec la probabilité 1 - p
E[X] = p × I
Var[X] = p × (1 - p) × I²
```

Un impact positif peut représenter une menace et un impact négatif une opportunité. `p = 0`,
`p = 1` et `I = 0` sont traités comme des cas déterministes sans consommer l'état du générateur.

## Noms et alias

Les noms canoniques sont `triangular`, `pert`, `uniform`, `normal`, `lognormal` et `event`. La casse
et les espaces externes sont ignorés. Les alias pris en charge sont :

- `beta-pert`, `beta_pert`, `beta pert` pour `pert` ;
- `log-normal`, `log_normal`, `log normal` pour `lognormal` ;
- `event-based`, `event_based`, `event based`, `eventual`, `bernoulli`, `bernoulli-event` et
  `bernoulli_event` pour `event`.

Les noms des postes sont nettoyés de leurs espaces externes et doivent être uniques sans tenir
compte de la casse.

## Agrégation

Chaque poste est simulé sous forme d'un vecteur NumPy complet. Les vecteurs sont additionnés ligne
par ligne pour produire la distribution du coût ou du délai total. Aucune boucle Python ne porte
sur les tirages individuels ; la seule boucle du moteur porte sur les postes du registre.

## Percentiles

Les percentiles donnent les seuils sous lesquels se trouve la proportion correspondante des
résultats simulés. La configuration accepte un tuple non vide de niveaux finis strictement compris
entre 0 et 1. Le libellé conserve les décimales significatives : `0.50` devient `P50`, `0.951`
devient `P95.1` et `0.995` devient `P99.5`. Les niveaux dupliqués et toute collision de libellé
résiduelle sont refusés ; aucun quantile n'en écrase un autre dans le résumé.

## Registre Excel et baseline

Le schéma Excel `1.0` est une frontière d'entrée, pas une nouvelle méthode probabiliste. Une ligne
active validée devient exactement un `RiskItem`. Les lignes désactivées sont ignorées avant la
validation de leurs paramètres. Toutes les unités actives doivent correspondre à `default_unit`
(comparaison sans tenir compte de la casse) ; aucune conversion monétaire ou temporelle n'est
effectuée.

`baseline_estimate` est une référence finie facultative pour comparer les résultats à une
estimation de départ. Elle n'entre pas dans l'équation d'agrégation et n'est jamais ajoutée
implicitement. Si la baseline doit faire partie du total, elle doit être représentée par un poste
déterministe explicite. Cette décision évite une double comptabilisation silencieuse.

## Value at Risk

Dans ce projet, la VaR au niveau de confiance `q` correspond au quantile `q` de la distribution
simulée. Elle représente donc un coût au percentile choisi, pas une dérive par rapport à un budget
de référence.

## Loi des grands nombres

Quand le nombre de tirages augmente, les estimations empiriques des quantiles et des moments se
stabilisent. Le projet ne fournit pas encore de diagnostic automatique de convergence.

## Fonctionnalités hors périmètre actuel

Les corrélations, la décomposition de Cholesky, l'analyse de sensibilité, le diagramme de tornade,
la courbe en S, la convergence automatique, la comparaison de scénarios et les exports PDF ou
PowerPoint ne sont pas implémentés. L'import Excel versionné, en revanche, est opérationnel via la
CLI et le service applicatif.
