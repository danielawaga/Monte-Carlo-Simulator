# Registre synthétique réaliste — Projet de bâtiment administratif

## 1. Objectif du document

Ce document consolide les décisions prises pour créer un premier registre de risques
synthétique destiné au simulateur Monte Carlo. Il doit permettre de reprendre le travail dans
une nouvelle session sans perdre le raisonnement, les hypothèses ni les valeurs proposées.

L'objectif n'est pas de présenter ces données comme celles d'un projet réel. Il s'agit de
construire un **cas d'étude synthétique réaliste**, reproductible, explicable et exempt de
données confidentielles. Le registre servira à valider le workflow Excel, les simulations, les
percentiles, l'analyse de sensibilité et la comparaison à une estimation de référence.

## 2. Cas d'étude retenu

Le cas proposé est la construction fictive d'un bâtiment administratif R+1 d'environ 700 m²
au Maroc.

- Type d'analyse : `cost`
- Unité commune : `MAD`
- Périmètre : travaux, études, contrôle et risques de réalisation
- Montants : hors taxes
- Exclusions : terrain, financement et fiscalité
- Schéma Excel attendu : `1.0`
- Nature des données : hypothèses pédagogiques synthétiques

La structure des lots est inspirée des familles observées dans les bordereaux publics de
bâtiment : terrassements, fondations, béton armé, maçonnerie, étanchéité, installations
techniques, finitions et aménagements extérieurs. Les montants ne sont toutefois pas repris
d'un marché réel et ne constituent pas des références officielles de prix.

## 3. Clarification sur les trois scénarios

Il n'est pas prévu de construire immédiatement trois registres entièrement différents. La
démarche recommandée consiste à partir d'un même registre et à modifier progressivement une
famille d'hypothèses :

1. scénario de référence sans corrélations ;
2. variante avec corrélations modérées et justifiées ;
3. variante de stress avec hypothèses plus défavorables.

Cette démarche facilite l'interprétation, car les différences entre les résultats peuvent être
attribuées aux hypothèses modifiées plutôt qu'à un changement complet de projet.

## 4. Postes continus proposés

Les montants du tableau sont exprimés en **milliers de MAD** pour faciliter la lecture. Dans le
classeur Excel, ils seront saisis en MAD complets.

| Poste | Distribution | Minimum | Plus probable / moyenne | Maximum / écart-type | Justification |
| --- | --- | ---: | ---: | ---: | --- |
| Études et contrôles | Normale | — | 250 | 20 | Prestations relativement contractuelles et prévisibles ; l'incertitude est faible et approximativement symétrique. |
| Installation du chantier | PERT | 220 | 280 | 380 | Dépend de la durée, des équipements temporaires, de la sécurité et de l'organisation du chantier. |
| Terrassement | PERT | 300 | 400 | 650 | Forte incertitude sur la nature du sol, les volumes extraits, les évacuations et les moyens nécessaires. |
| Fondations et gros œuvre | PERT | 1 600 | 1 900 | 2 500 | Poste principal, exposé aux quantités de béton et d'acier ainsi qu'à la productivité. |
| Étanchéité et toiture | Triangulaire | 400 | 500 | 700 | Les surfaces sont identifiables, mais les détails techniques et traitements peuvent évoluer. |
| Façades et menuiseries | PERT | 650 | 750 | 1 000 | Sensibilité aux dimensions finales, aux matériaux, au vitrage et aux fournisseurs. |
| Électricité | PERT | 550 | 650 | 850 | Dépend du niveau d'équipement, des réseaux et des éventuelles modifications techniques. |
| Plomberie et sanitaires | PERT | 400 | 480 | 650 | Incertitude sur les quantités et la gamme des appareils sanitaires. |
| Climatisation et ventilation | PERT | 450 | 550 | 800 | Équipements spécialisés exposés au dimensionnement et aux variations de prix. |
| Revêtements et finitions | PERT | 800 | 950 | 1 300 | Choix tardifs, reprises, exigences esthétiques et évolution de la qualité attendue. |
| Aménagements extérieurs | PERT | 350 | 450 | 700 | Périmètre souvent moins défini en début de projet et dépendant des conditions du site. |
| Supervision du chantier | Normale | — | 300 | 45 | Coût relativement régulier, mais sensible à une prolongation de la durée du chantier. |

Pour les lignes normales, `mean` et `standard_deviation` sont utilisés. Les champs `minimum`,
`most_likely` et `maximum` restent vides. Pour les lignes PERT et triangulaire, les trois
estimations sont utilisées et les champs de moyenne restent vides.

## 5. Risques événementiels proposés

Un risque événementiel vaut zéro s'il ne se produit pas et prend la valeur de son impact s'il
se produit. Un impact positif est une menace ; un impact négatif est une opportunité.

| Événement | Probabilité | Impact en milliers de MAD | Justification |
| --- | ---: | ---: | --- |
| Sol plus difficile que prévu | 12 % | +350 | Risque crédible lorsque les reconnaissances géotechniques sont encore incomplètes. |
| Hausse exceptionnelle des matériaux | 20 % | +450 | Choc commun possible sur l'acier, le ciment, les équipements et les finitions. |
| Retard administratif ou de raccordement | 18 % | +250 | Peut prolonger la supervision, les installations temporaires et certains contrats. |
| Modification tardive du programme | 15 % | +300 | Peut entraîner études supplémentaires, reprises et nouvelles commandes. |
| Défaillance ou remplacement d'un fournisseur | 10 % | +220 | Peut provoquer un nouvel achat, une différence de prix ou un retard. |
| Négociation commerciale favorable | 25 % | -120 | Opportunité de réduction des coûts par remise ou regroupement de commandes. |

Ces probabilités sont des hypothèses pédagogiques. Elles devront être identifiées comme telles
dans la colonne `notes` du registre et ne devront pas être présentées comme des statistiques
observées.

## 6. Estimation centrale et baseline

La somme des valeurs centrales ou moyennes des douze postes continus est :

```text
250 + 280 + 400 + 1 900 + 500 + 750 + 650 + 480 + 550 + 950 + 450 + 300
= 7 460 milliers de MAD
= 7 460 000 MAD
```

La baseline budgétaire proposée est :

```text
7 750 000 MAD
```

Elle inclut donc une réserve initiale de 290 000 MAD, soit environ 3,9 % de l'estimation
centrale des travaux continus. Cette réserve volontairement limitée permet de poser une
question métier utile :

> Le budget de 7 750 000 MAD offre-t-il une confiance suffisante, notamment aux niveaux P80
> et P90 ?

Dans le simulateur, `baseline_estimate` est uniquement une valeur de comparaison. Elle n'est
jamais ajoutée aux tirages. Les postes continus représentent déjà les coûts du projet ; ajouter
la baseline au total provoquerait une double comptabilisation.

## 7. Règles utilisées pour choisir les valeurs

### 7.1. Définir trois estimations crédibles

Pour chaque poste à trois points :

- le minimum correspond à un déroulement favorable mais plausible ;
- la valeur la plus probable correspond à l'estimation centrale raisonnable ;
- le maximum correspond à un déroulement défavorable mais encore crédible.

Les catastrophes rares ne doivent pas être absorbées artificiellement dans le maximum. Elles
sont représentées séparément sous forme de risques événementiels.

### 7.2. Adapter la dispersion à la maturité

Les fourchettes ne doivent pas être identiques pour tous les postes.

| Niveau de maturité | Minimum indicatif | Maximum indicatif |
| --- | ---: | ---: |
| Poste bien défini ou contractualisé | -5 % à -10 % | +10 % à +15 % |
| Poste moyennement défini | -10 % à -15 % | +20 % à +30 % |
| Poste encore incertain | -15 % à -25 % | +35 % à +60 % |

Les études sont donc peu dispersées, tandis que le terrassement, les finitions et les
aménagements extérieurs ont des plages plus larges.

### 7.3. Conserver une asymétrie réaliste

Les coûts ont généralement plus de possibilités d'augmenter que de diminuer : quantités
supplémentaires, reprises, retards, inflation, changement de spécification ou indisponibilité
d'un fournisseur. Le maximum est donc souvent plus éloigné de la valeur probable que le
minimum.

### 7.4. Éviter la fausse précision

Les montants doivent être arrondis à 10 000 ou 50 000 MAD. Une valeur comme 647 382 MAD
donnerait une impression de précision qui n'est pas justifiée par un cas synthétique.

## 8. Choix des distributions

### Beta-PERT

PERT est retenue pour la majorité des lots. Elle convient lorsqu'une borne favorable, une
valeur la plus probable et une borne défavorable peuvent être formulées. Elle concentre
davantage les tirages autour de la valeur probable que la loi triangulaire et évite de donner
le même poids à toute la plage.

Le paramètre `lambda_shape` peut rester vide afin d'utiliser la valeur par défaut `4.0` du
simulateur.

### Triangulaire

La loi triangulaire est utilisée pour l'étanchéité et la toiture afin de conserver au moins un
poste fondé sur une hypothèse simple à trois points. Elle est pertinente lorsque l'on dispose de
peu d'informations au-delà des bornes et du mode.

### Normale

La loi normale est réservée aux études et à la supervision, dont les coûts sont supposés plus
stables et approximativement symétriques. Les écarts-types restent faibles devant les moyennes,
ce qui rend la probabilité de tirages négatifs négligeable.

Elle ne doit pas être employée pour des événements rares ou des coûts fortement asymétriques.

### Événement

La loi événementielle représente les menaces et opportunités discrètes. Elle sépare clairement
la probabilité d'occurrence de l'impact financier et permet d'éviter de surcharger les maxima
des postes continus.

## 9. Corrélations de la variante 2

La variante 1 reste la référence sans corrélation. La variante 2, désormais développée et validée,
conserve les mêmes dix-huit postes, distributions marginales, baseline, nombre de tirages et graine.
Elle ajoute quatre relations modérées et explicables :

| Relation | Coefficient latent | Raisonnement |
| --- | ---: | --- |
| Terrassement — fondations et gros œuvre | 0,30 | Des conditions de sol défavorables peuvent affecter les deux lots. |
| Fondations et gros œuvre — hausse des matériaux | 0,50 | Le gros œuvre consomme beaucoup de béton et d'acier. |
| Électricité — plomberie | 0,25 | Les modifications d'aménagement peuvent affecter plusieurs réseaux. |
| Supervision — retard administratif | 0,40 | Un retard augmente généralement la durée de mobilisation de la supervision. |

La matrice complète est symétrique, sa diagonale vaut 1 et elle est strictement définie positive.
Les coefficients représentent les dépendances latentes de la copule gaussienne. Pour un événement
binaire, la transformation en `0/impact` crée des ex æquo et atténue normalement la corrélation de
rang observée. Ces hypothèses restent synthétiques et devront être recalibrées si des historiques ou
un jugement expert deviennent disponibles.
## 10. Méthode d'anonymisation d'un futur registre réel

Si un registre réel devient disponible plus tard, il pourra être anonymisé en :

- remplaçant le projet par `Projet A` ;
- remplaçant les entreprises et fournisseurs par des identifiants génériques ;
- supprimant les noms, contacts, numéros de contrats et localisations précises ;
- renommant les postes susceptibles d'identifier le client ;
- multipliant tous les montants par un même coefficient confidentiel ;
- conservant les rapports relatifs, les probabilités et les corrélations ;
- arrondissant les valeurs ;
- supprimant les notes contenant des informations sensibles ;
- conservant le fichier réel hors du dépôt Git.

L'utilisation d'un coefficient commun masque les montants absolus tout en préservant l'intérêt
statistique du cas.

## 11. Sources publiques d'inspiration

Les sources suivantes servent à justifier la structure générale et la méthode, et non les
montants synthétiques :

- Bordereau public marocain comportant terrassements, gros œuvre, assainissement, béton,
  maçonnerie et autres familles de travaux :
  <https://habous.gov.ma/fr/index.php?cf_id=38&link_id=413&option=com_mtree&task=att_download>
- Haut-Commissariat au Plan, indices des prix et de la production :
  <https://www.hcp.ma/Indices-des-prix-et-production_r343.html>
- Portail Open Data du Maroc, données relatives aux indices des prix des matériaux de
  construction :
  <https://www.data.gov.ma/data/dataset/?organization=matnuhpv&tags=indice+des+prix&tags=mat%C3%A9riaux+de+construction>
- HM Treasury, recommandations sur le biais d'optimisme lorsque les données historiques sont
  insuffisantes :
  <https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias>
- Homes England, approche par classe de référence, contingence et niveaux P50/P80 :
  <https://www.gov.uk/government/publications/optimism-bias-and-contingency-at-homes-england/optimism-bias-and-contingency-at-homes-england-accessible-version>

## 12. État de réalisation et reproduction

Les trois variantes sont réalisées :

1. variante 1 sans corrélation ;
2. variante 2 avec quatre corrélations modérées ;
3. variante 3 conservant ces corrélations avec un stress ciblé sur certaines valeurs.

Chaque simulation utilise 10 000 tirages et la graine 42. Le workflow Excel produit maintenant huit
artefacts : résumé statistique, histogramme, courbe en S, table de décision par percentile,
diagnostic de convergence, sensibilité de Spearman, diagramme tornado et comparaison à la
baseline.

La validation comprend 44 contrôles fonctionnels : distributions, reproductibilité, corrélations,
comparaison des variantes, erreurs Excel et recalcul indépendant des sorties. La suite automatisée
comprend 337 tests et la couverture mesurée lors de la fusion atteint 92,18 %.

Les classeurs sont générés avec `openpyxl` à partir du modèle public du dépôt. Ils restent hors de
Git conformément à la politique de confidentialité, mais les scripts sous `scripts/case_study/`
permettent de les reconstruire. Les commandes exactes et l'ordre complet sont documentés dans le
README de ce dossier. Les preuves tabulaires publiées se trouvent sous `docs/validation/` et le
rapport évolutif final sous `reports/case_study/`.