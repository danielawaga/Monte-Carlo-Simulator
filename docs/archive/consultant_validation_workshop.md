# Atelier de validation consultant — Semaine 3

## But

Valider la crédibilité métier des hypothèses et l'utilité décisionnelle des sorties Monte Carlo. Cet atelier ne sert pas à expliquer toutes les mathématiques : il doit faire ressortir les hypothèses contestables, les dépendances oubliées et les décisions que les résultats permettent réellement de prendre.

## Préparation obligatoire

- Utiliser un registre anonymisé et autorisé, ou rester sur le cas synthétique fourni.
- Envoyer avant la séance une page contenant : baseline actuelle, P50/P80/P90, probabilité de dépassement, trois risques dominants et matrice de corrélation.
- Ne jamais charger de données client dans le dépôt Git.
- Vérifier que `correlation_diagnostics.csv` indique `strict-no-repair` et `automatic_repair_applied = False`.

## Déroulé — 45 minutes

| Temps | Séquence | Décision attendue |
| ---: | --- | --- |
| 0–5 min | Rappeler le projet, l'unité, la baseline et la source des hypothèses | Périmètre confirmé |
| 5–15 min | Revue des estimations min / probable / max et des risques événementiels | Paramètres à conserver ou revoir |
| 15–25 min | Revue des corrélations par paires, uniquement pour les dépendances explicables | Corrélations justifiées, supprimées ou ajustées |
| 25–35 min | Lecture de la S-curve, des P50/P80/P90 et de la réserve recommandée | Niveau de confiance utile au pilotage |
| 35–42 min | Revue du tornado Spearman et des actions de mitigation | Risques prioritaires et responsables |
| 42–45 min | Décision de validation et prochaines étapes | Accepté, accepté sous réserves ou rejeté |

## Questions à poser

### Estimations

1. Quel scénario concret correspond au minimum, au plus probable et au maximum ?
2. Une même hypothèse est-elle comptée dans plusieurs postes ?
3. Le maximum représente-t-il un scénario plausible ou seulement une borne confortable ?
4. Quels postes sont tirés d'historique, d'un devis, d'un jugement expert ou d'une convention ?
5. Existe-t-il un biais d'optimisme évident dans la baseline actuelle ?

### Corrélations

1. Quel mécanisme commun explique la dépendance entre les deux postes ?
2. La corrélation reste-t-elle valable dans les scénarios défavorables ?
3. Le signe est-il cohérent avec le mécanisme décrit ?
4. La valeur peut-elle être défendue devant un comité de pilotage ?
5. En cas de doute, faut-il mettre zéro plutôt qu'une précision artificielle ?

Le moteur refuse les matrices non strictement définies positives. Il ne projette, ne corrige et ne perturbe jamais silencieusement une matrice fournie.

### Résultats

1. Le P50 semble-t-il compatible avec les projets comparables ?
2. Quelle probabilité de dépassement est acceptable pour la décision étudiée ?
3. Le P80 ou le P90 change-t-il réellement une décision de budget, de contrat ou de mitigation ?
4. Les trois premiers risques du tornado correspondent-ils à l'expérience terrain ?
5. Quel résultat paraît surprenant, et quelle hypothèse pourrait l'expliquer ?

## Critères de validation

Une séance est considérée comme concluante seulement si :

- chaque paramètre contesté possède un propriétaire et une action ;
- chaque corrélation non nulle possède une justification métier écrite ;
- la baseline et le niveau de confiance retenu sont explicitement distingués ;
- les consultants comprennent que Spearman classe une association monotone, pas une causalité ;
- le statut final est consigné : `accepted`, `accepted_with_actions` ou `rejected` ;
- aucune donnée confidentielle non autorisée n'est conservée dans le dépôt.

## Traces à conserver

Utiliser `data/templates/consultant_validation_log.csv` pour consigner uniquement des informations anonymisées. Joindre au compte rendu :

- la version ou le commit du moteur ;
- le hash ou l'identifiant interne du registre, sans joindre le registre confidentiel ;
- les fichiers `percentile_decision_table.csv`, `convergence_diagnostics.csv`, `correlation_diagnostics.csv` et `sensitivity_summary.csv` ;
- les décisions, responsables et échéances ;
- la date prévue de revalidation après correction.

## Statut du cas synthétique

Le script `python -m scripts.run_s3_acceptance_case` valide le chemin logiciel et les invariants numériques. Il ne remplace pas cette séance : la crédibilité des hypothèses réelles ne peut être validée automatiquement.
