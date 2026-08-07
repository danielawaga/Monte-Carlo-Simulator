# Note méthodologique vulgarisée

## Pourquoi utiliser Monte Carlo ?

Une prévision unique donne l'impression qu'un projet possède un coût ou un délai exact. En réalité, chaque poste contient de l'incertitude : variation de quantités, prix fournisseurs, rendement, retards, aléas techniques, événements rares, etc.

La simulation Monte Carlo remplace le chiffre unique par une **distribution de résultats possibles**. À chaque tirage, le moteur génère une valeur plausible pour chaque poste selon les hypothèses du registre, additionne les postes et obtient un coût ou un délai total. Répété des milliers de fois, ce mécanisme permet d'estimer des percentiles et des probabilités de dépassement.

Le résultat ne prédit pas l'avenir. Il répond à une question conditionnelle : **si les hypothèses et dépendances saisies décrivent correctement l'incertitude, quelle distribution de résultat en découle ?**

## 1. Les distributions représentent des hypothèses

Le projet accepte six familles de distributions.

- **Triangulaire** : minimum, valeur la plus probable, maximum. Simple à expliquer et adaptée à un jugement expert rapide.
- **Beta-PERT** : mêmes trois points mais davantage de masse autour de la valeur la plus probable. Utile lorsque les extrêmes sont plausibles mais moins probables.
- **Uniforme** : toutes les valeurs entre deux bornes ont la même densité. À utiliser seulement lorsqu'il n'existe réellement aucune valeur plus probable.
- **Normale** : distribution symétrique autour d'une moyenne. Elle n'est pas bornée ; elle peut donc produire des valeurs négatives.
- **Log-normale** : distribution strictement positive et asymétrique. Elle convient à des grandeurs dont les dépassements élevés sont possibles mais moins fréquents.
- **Événementielle** : un événement se produit avec une probabilité `p` et génère un impact donné, sinon l'impact est nul.

Le choix d'une distribution ne doit pas être automatique. Il doit pouvoir être expliqué par la nature du poste et, si possible, par des données historiques ou un raisonnement métier documenté.

## 2. Agrégation des postes

Chaque poste est simulé sur le même nombre de tirages. Pour un tirage donné, les valeurs de tous les postes sont additionnées pour produire le total du projet. Le moteur travaille de manière vectorisée avec NumPy afin d'exécuter efficacement 10 000 tirages ou davantage.

Une baseline saisie dans le fichier Excel n'est **pas** ajoutée à ce total. Elle reste une référence externe servant à comparer la distribution simulée au budget ou au délai actuellement retenu.

## 3. Corrélations : éviter l'indépendance artificielle

Deux postes peuvent varier ensemble. Par exemple, un retard de conception peut augmenter à la fois les heures d'ingénierie et les coûts de coordination. Supposer ces postes indépendants peut sous-estimer ou déformer le risque total.

Le moteur utilise une **copule gaussienne** :

1. il génère des variables normales corrélées ;
2. la dépendance est imposée via une décomposition de Cholesky ;
3. les valeurs sont transformées vers les distributions marginales de chaque poste.

La matrice fournie doit être strictement définie positive. Le moteur applique une politique volontairement stricte : une matrice invalide est rejetée avec un diagnostic au lieu d'être réparée silencieusement. Cette règle préserve la traçabilité des hypothèses.

Une corrélation non nulle doit toujours posséder une justification métier. Ajouter des coefficients « pour faire réaliste » crée une précision artificielle.

## 4. Percentiles et niveau de confiance

Le percentile `Px` est la valeur sous laquelle se trouvent environ `x %` des tirages simulés.

- `P50` : moitié des tirages sont en dessous, moitié au-dessus ;
- `P80` : environ 80 % des tirages sont en dessous ;
- `P90` : environ 90 % des tirages sont en dessous ;
- `P95` : environ 95 % des tirages sont en dessous.

Dans ce projet, la Value at Risk au niveau `q` correspond au quantile `q` de la distribution du total. Ce n'est pas automatiquement « la marge à ajouter ».

Si une baseline existe, la réserve affichée au niveau `Px` vaut :

```text
reserve(Px) = max(Px - baseline, 0)
```

La probabilité de dépassement est estimée par la proportion stricte de tirages satisfaisant :

```text
total > baseline
```

Une valeur exactement égale à la baseline n'est donc pas comptée comme dépassement.

## 5. Lire la S-curve

La S-curve est la fonction de répartition empirique du total simulé. Pour une valeur donnée sur l'axe horizontal, l'axe vertical indique la proportion de tirages qui ne dépassent pas cette valeur.

Elle permet de répondre directement à des questions de pilotage :

- « Avec ce budget, quelle probabilité avons-nous de ne pas le dépasser ? »
- « Quel budget correspond à un niveau de confiance de 80 % ? »

Elle est souvent plus utile en comité que l'histogramme seul, car elle relie immédiatement une valeur à une probabilité cumulative.

## 6. Sensibilité de Spearman et tornado

Pour chaque poste, le moteur calcule la corrélation de rang de Spearman entre ses tirages et le total simulé. Le classement utilise la valeur absolue du coefficient.

Une grande valeur absolue signifie que les variations de ce poste sont fortement associées aux variations du total. Le signe indique la direction de l'association.

Trois limites sont importantes :

1. **association n'est pas causalité** ;
2. avec des postes corrélés, plusieurs variables peuvent partager la même source d'importance ;
3. les coefficients ne constituent pas une décomposition additive de variance et ne doivent pas être normalisés pour « faire 100 % ».

Un poste déterministe produit une série constante. Sa corrélation de Spearman est indéfinie ; il est signalé explicitement et exclu du tornado par défaut.

## 7. Convergence numérique

Le diagnostic de convergence recalcule le percentile cible sur des blocs cumulés de tirages. Il observe la variation relative entre deux estimations successives et signale un point d'arrêt lorsque la variation reste suffisamment faible pendant plusieurs blocs.

Ce contrôle répond à la question : **avons-nous fait assez de tirages pour stabiliser numériquement le quantile ?**

Il ne répond pas à la question : **nos hypothèses sont-elles bonnes ?** Une simulation parfaitement convergée peut rester inutile si les distributions, les bornes ou les corrélations sont mal estimées.

## 8. Ce qu'il faut valider avec les consultants

Avant de présenter un résultat comme décisionnel, vérifier au minimum :

- la provenance des min / plus probable / max ou des moyennes et écarts-types ;
- l'absence de double comptage entre postes et risques événementiels ;
- la justification des corrélations non nulles ;
- la cohérence de la baseline avec le périmètre simulé ;
- la crédibilité des trois premiers risques du tornado ;
- le niveau de confiance réellement pertinent pour la décision étudiée.

Le cas synthétique du dépôt valide le fonctionnement logiciel et les invariants numériques. Il ne valide pas la crédibilité d'un cas client réel.

## 9. Reproductibilité et traçabilité

Une restitution devrait conserver :

- le fichier source autorisé ou son identifiant interne ;
- la version / le commit du moteur ;
- le nombre de tirages ;
- la seed ;
- le niveau de confiance retenu ;
- les artefacts produits ;
- les décisions ou corrections d'hypothèses décidées lors de la revue.

À registre, ordre des postes, configuration et seed identiques, le moteur reproduit les mêmes tirages.

## 10. Limites actuelles

Le moteur fournit aujourd'hui l'import Excel, les six distributions, les corrélations, les percentiles, la comparaison à la baseline, la S-curve, la sensibilité Spearman, le tornado et la convergence numérique.

Les extensions prévues pour les semaines suivantes restent notamment : comparaison de scénarios / mode what-if, exports décisionnels PDF ou PowerPoint et calibration sur données historiques autorisées.
