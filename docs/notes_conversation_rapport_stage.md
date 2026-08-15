# Notes de référence pour le rapport de stage

## Objet du document

Cette note conserve les éléments clés discutés à propos du projet
`Monte-Carlo-Simulator`. Elle sert de mémoire de travail pour la rédaction du rapport de
stage. Elle distingue volontairement les faits vérifiables dans le dépôt, leur justification
et les limites qui devront être expliquées dans le rapport final.

État documentaire de référence : 9 août 2026 pour les réalisations attestées par les rapports
hebdomadaires et l'historique Git.

## 1. Domaine et problème traité

Le projet se situe à la croisée de la gestion des risques, de l'estimation probabiliste des
coûts et délais, de l'aide quantitative à la décision et du développement logiciel appliqué au
conseil.

Une estimation ponctuelle, éventuellement complétée par une marge forfaitaire de 15 ou 20 %,
ne montre ni la probabilité de dépassement ni les causes principales de l'exposition. La
simulation Monte Carlo remplace ce chiffre unique par une distribution de résultats possibles.
Elle permet notamment de calculer P50, P80 et P90, la probabilité de dépasser une baseline, la
réserve correspondant à un niveau de confiance et les facteurs les plus influents.

Idée directrice à reprendre dans le rapport : le projet déplace la discussion de « combien de
marge ajouter ? » vers « quelles hypothèses créent l'exposition, quel niveau de confiance
souhaitons-nous et sur quels facteurs pouvons-nous agir ? ».

## 2. Feuille de route initiale

Le stage était planifié sur six semaines, du 13 juillet au 23 août 2026 :

1. S1 - fondations et preuve de concept ;
2. S2 - moteur structuré, six distributions et entrée Excel ;
3. S3 - corrélations, sensibilité, convergence et restitution décisionnelle ;
4. S4 - interface Streamlit, qualité, documentation et transmission ;
5. S5 - marge de planning, retours et extensions ;
6. S6 - clôture, passation, cas documenté et rapport de stage.

La méthode retenue était une approche en spirale : chaque semaine devait laisser une version
complète, testable et démontrable. Git, les tests automatiques et la séparation des couches ont
été introduits tôt afin de limiter les régressions et la dépendance à une seule personne.

## 3. Chronologie des réalisations

### Semaine 1 - construire le socle

Réalisations principales :

- dépôt Git, environnement Python et première boucle Monte Carlo ;
- six distributions : triangulaire, Beta-PERT, uniforme, normale, log-normale et
  événementielle ;
- tirages NumPy vectorisés et graine reproductible ;
- registre Excel versionné et validation des saisies ;
- résumé statistique, histogramme, ligne de commande et premiers guides ;
- 241 tests et couverture annoncée de 92,79 % au 17 juillet.

Justification : commencer par un parcours de bout en bout permettait de valider le principe avant
d'ajouter les fonctions avancées. Excel rendait la saisie accessible aux consultants. La graine
et les tests rendaient les résultats reproductibles et les évolutions contrôlables.

Limite : les données étaient fictives et les postes supposés indépendants.

### Semaine 2 - expliquer le risque et le comparer au budget

Réalisations principales :

- matrice de corrélation optionnelle dans Excel ;
- simulation dépendante par copule gaussienne et Cholesky ;
- analyse de sensibilité de Spearman et diagramme de tornade ;
- comparaison à la baseline, probabilité de dépassement et réserves P80/P90 ;
- intégration dans le workflow Excel et passage à 325 tests.

Justification : l'indépendance peut sous-estimer la dispersion lorsque plusieurs coûts réagissent
au même facteur. La sensibilité répond à « où agir ? ». La baseline traduit les percentiles en
une information directement budgétaire.

Précaution : Spearman mesure une association monotone, pas une causalité. La baseline est une
référence de comparaison ; elle n'est jamais ajoutée au total simulé.

### Semaine 3 - consolider l'aide à la décision

Réalisations principales :

- diagnostic numérique strict des matrices de corrélation ;
- politique de rejet des matrices invalides sans réparation silencieuse ;
- S-curve, table de décision P50/P80/P90 et diagnostic de convergence ;
- cas synthétique d'un bâtiment administratif avec variantes indépendante, corrélée et stressée ;
- protocole d'acceptation reproductible et préparation de la validation consultant ;
- 341 tests et 44 contrôles fonctionnels réussis sur 44.

Justification : réparer silencieusement une matrice aurait changé les hypothèses métier. La
S-curve relie directement un budget à sa probabilité de non-dépassement. La convergence vérifie
la stabilité numérique du percentile, sans valider la qualité métier des entrées.

Résultat pédagogique du cas synthétique : les corrélations ont peu déplacé la moyenne mais ont
augmenté la dispersion et les quantiles prudents. Dans le scénario stressé, le P80 atteignait
environ 8,993 M MAD contre une baseline de 7,75 M MAD, soit une exposition proche de
1,243 M MAD. Ce montant devait nourrir une discussion et non devenir une recommandation
automatique.

### Semaine 4 - rendre le moteur utilisable et transmissible

Réalisations principales :

- interface Streamlit avec upload Excel, paramètres, niveau P50/P80/P90/P95 et lancement ;
- métriques de décision, cinq onglets, graphiques Plotly et téléchargement des résultats ;
- thèmes clair et sombre, cohérence des unités et correction de la portabilité des ressources ;
- guide de prise en main, note méthodologique, passation et trame de restitution ;
- vérification depuis un clone propre, CI Python 3.11/3.12 et 357 tests réussis.

Justification : l'obstacle principal n'était plus mathématique mais ergonomique. L'interface est
restée une couche mince appelant le même service que la CLI afin de ne pas dupliquer les règles
probabilistes.

Limite persistante : la validation auprès de consultants sur un registre réel autorisé n'était
pas encore réalisée. Les semaines 5 et 6 restaient planifiées, mais aucune réalisation
postérieure au 9 août n'était attestée dans les sources consultées lors de cette conversation.

## 4. Vectorisation du moteur

Avec `n` simulations et `d` postes, le moteur construit conceptuellement une matrice
`X` de forme `(n, d)`. Chaque ligne est un scénario complet et chaque colonne un poste de
risque. Le total d'un scénario est la somme de sa ligne.

Pour le cas indépendant, un seul `numpy.random.Generator` est créé à partir de la graine. Chaque
distribution reçoit `size=number_of_simulations` et renvoie directement un vecteur NumPy complet.
Le moteur boucle sur les postes, mais jamais sur les 10 000 scénarios individuels. Les colonnes
sont ensuite additionnées par une opération vectorisée.

Exemple uniforme entre `a` et `b` : le moteur génère un vecteur `U` dans `[0, 1[` puis calcule
`X = a + (b - a) * U`. Pour une loi triangulaire, il applique vectoriellement l'inverse de la
fonction de répartition à partir de minimum, valeur la plus probable et maximum.

La vectorisation améliore surtout les performances ; elle ne supprime pas l'incertitude
d'échantillonnage.

## 5. Tirage des vecteurs corrélés

Le workflow corrélé est le suivant :

1. générer une matrice normale indépendante de forme `(10000, d)` ;
2. décomposer la matrice de corrélation `R` sous la forme `R = L Lᵀ` ;
3. calculer `Z_corrélé = Z Lᵀ` ;
4. transformer les normales corrélées en probabilités avec la fonction de répartition normale ;
5. appliquer à chaque colonne la fonction quantile de sa distribution métier.

Cette méthode sépare la structure de dépendance, portée par la copule gaussienne, et la forme de
chaque loi marginale. Les probabilités sont bornées juste à l'intérieur de l'intervalle ouvert
`(0, 1)` afin d'éviter des quantiles infinis.

« Sans biais » ne signifie pas que 10 000 tirages reproduisent exactement la théorie. Un
échantillon fini varie normalement autour des moments et quantiles théoriques. La reproductibilité
vient de la graine ; la stabilité est étudiée par le diagnostic de convergence. Les biais les plus
préoccupants restent ceux des hypothèses : risque oublié, borne optimiste, mauvaise loi ou
corrélation mal estimée.

## 6. Sens du mot « uniformisation »

Le projet ne transforme pas toutes les hypothèses en lois uniformes. Une estimation triangulaire,
PERT, normale ou événementielle conserve sa nature.

Trois opérations distinctes doivent être expliquées :

- **normalisation du format** : noms canoniques, nombres finis, probabilités entre 0 et 1,
  paramètres obligatoires, unités cohérentes et alignement des noms ;
- **transformation uniforme intermédiaire** : la copule représente temporairement les tirages par
  des probabilités dans `(0, 1)`, avant de les reconvertir avec la fonction quantile de la loi
  demandée ;
- **contrôle des unités** : le moteur empêche leur mélange dans un même run, mais n'effectue aucune
  conversion de devise et ne centre-réduit pas les montants métier.

Cette distinction évite d'affirmer à tort que les valeurs du consultant sont modifiées ou que tous
les montants deviennent équiprobables.

## 7. Couverture, tests et fiabilité

La couverture proche de 92 % mesure la proportion du code exécutée par la suite de tests. Elle ne
mesure pas la probabilité que le moteur ait raison et encore moins la précision de la prévision
réelle.

Il faut distinguer :

- **couverture du code** : lignes parcourues par les tests ;
- **réussite des tests** : scénarios programmés dont les assertions réussissent ;
- **exactitude numérique** : conformité à des propriétés mathématiques connues ;
- **validité métier** : réalisme des hypothèses, qui reste à valider avec des spécialistes et des
  données autorisées.

Formulation recommandée : « Le moteur est fortement vérifié sur le plan logiciel et numérique,
mais sa validité prédictive dépend de la qualité et de la validation métier des hypothèses
d'entrée. »

Les plus de 300 tests couvrent notamment : distributions et cas limites, paramètres invalides,
configuration, reproductibilité, moteur, corrélations, lecture Excel, unités, statistiques,
sensibilité, baseline, convergence, visualisations, exports, CLI et parcours de bout en bout.
Pytest compte séparément les variantes paramétrées ; une fonction exécutée sur six distributions
peut donc représenter six tests.

## 8. Artefacts produits

Un artefact est un fichier de sortie conservé pour l'analyse, la traçabilité ou le partage :

- `simulation_summary.csv` : moyenne, médiane, dispersion et percentiles ;
- `simulation_histogram.png` : forme de la distribution ;
- `simulation_s_curve.png` : probabilité cumulée de rester sous un budget ;
- `percentile_decision_table.csv` : montants, dépassements, écarts et réserves ;
- `convergence_diagnostics.csv` : stabilité du percentile selon le nombre de tirages ;
- `correlation_diagnostics.csv` : propriétés numériques de la matrice ;
- `sensitivity_summary.csv` : coefficients de Spearman et classement ;
- `sensitivity_tornado.png` : facteurs dominants ;
- `baseline_comparison.csv` : comparaison avec le budget de référence.

Ils proviennent du même run et de la même matrice de scénarios. Certains sont optionnels : sans
baseline, il n'y a pas de comparaison ; sans corrélations, il n'y a pas de diagnostic de matrice.

## 9. Points de vigilance pour le rapport final

- Ne pas présenter 92 % comme un taux de fiabilité ou de précision prédictive.
- Ne pas confondre convergence numérique et validation des hypothèses.
- Ne pas qualifier le cas synthétique de validation terrain.
- Ne pas présenter Spearman comme une causalité ou une décomposition de variance.
- Ne pas dire que la copule conserve exactement les corrélations linéaires finales pour toutes les
  marginales, notamment les risques binaires.
- Ne pas présenter P80 ou P90 comme un budget universellement recommandé : le niveau retenu dépend
  de la tolérance au risque et de la gouvernance.
- Bien distinguer résultats démontrés au 9 août et activités seulement prévues pour les semaines 5
  et 6.

## 10. Sources internes utiles

- `output/pdf/Feuille_de_route_1..pdf` ;
- rapports PDF des semaines 1 à 4 dans `output/pdf/` ;
- `README.md` ;
- `docs/methodology.md` et `docs/methodology_note.md` ;
- `docs/architecture.md` ;
- `docs/user_guide.md` et `docs/user_guide_30min.md` ;
- `docs/validation/` ;
- `src/monte_carlo_simulator/engine/` et `src/monte_carlo_simulator/distributions/` ;
- `tests/unit/` et `tests/integration/`.

