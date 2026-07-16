# Méthodologie

## Simulation Monte Carlo
La simulation Monte Carlo répète un grand nombre de tirages aléatoires pour approximer la distribution d'un résultat global. Le moteur utilise `numpy.random.Generator` avec une graine explicite afin de rendre chaque scénario reproductible.

## Lois prises en charge

### Triangulaire
La loi triangulaire est définie par trois valeurs : minimum, valeur la plus probable et maximum. Elle est adaptée lorsque les données historiques sont limitées mais qu'une expertise terrain permet de proposer une estimation à trois points.

### Beta-PERT
La loi PERT utilise les mêmes trois valeurs, mais concentre davantage la masse autour de la valeur la plus probable. L'implémentation transforme une loi bêta sur l'intervalle `[minimum, maximum]` avec un paramètre de forme par défaut `lambda = 4`.

Son espérance vaut :

```text
E[X] = (minimum + lambda × most_likely + maximum) / (lambda + 2)
```

### Uniforme
Toutes les valeurs comprises entre le minimum et le maximum ont la même densité. Cette loi convient lorsque seules des bornes crédibles sont disponibles et qu'aucune valeur centrale ne peut être privilégiée.

### Normale
La loi normale est paramétrée par une moyenne arithmétique et un écart-type. Elle n'est pas bornée : elle doit donc être utilisée avec prudence pour les coûts qui ne peuvent pas devenir négatifs.

### Log-normale
La loi log-normale produit uniquement des valeurs strictement positives. Les champs `mean` et `standard_deviation` du registre sont interprétés dans l'espace arithmétique, puis convertis en paramètres logarithmiques avant le tirage. Cette convention évite de demander aux consultants de renseigner des paramètres peu intuitifs.

### Risque événementiel
Un risque événementiel suit un modèle de Bernoulli :

```text
X = impact avec la probabilité p
X = 0 avec la probabilité 1 - p
```

L'impact peut être positif pour une menace ou négatif pour une opportunité.

## Agrégation
Chaque poste est simulé sous forme d'un vecteur NumPy. Les vecteurs sont additionnés ligne par ligne pour produire la distribution du coût ou du délai total. Le moteur évite les boucles sur les tirages ; la seule boucle restante porte sur le nombre de postes du registre.

## Percentiles
Les percentiles P50, P80 et P90 donnent les seuils sous lesquels se trouvent respectivement 50 %, 80 % et 90 % des résultats simulés.

## Value at Risk
Dans ce projet, la VaR au niveau de confiance `q` correspond au quantile `q` de la distribution simulée du coût total. Une convention de référence budgétaire devra être ajoutée pour distinguer clairement le coût au percentile choisi de la dérive par rapport au budget de base.

## Loi des grands nombres
Quand le nombre de tirages augmente, les estimations des quantiles et des moments deviennent plus stables. Une phase ultérieure ajoutera un diagnostic de convergence du P90 par blocs de tirages.

## Corrélations futures
Une étape future appliquera une matrice de corrélation et une décomposition de Cholesky afin de modéliser les dépendances entre postes. Les matrices invalides devront être détectées puis projetées vers une matrice semi-définie positive avant utilisation.
