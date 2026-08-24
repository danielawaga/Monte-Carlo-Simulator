# Restitution S4 — trame de démonstration

Durée cible : **10 à 15 minutes**. Public : consultants et maître de stage, sans prérequis mathématique.

## Message central

L'outil ne cherche pas à remplacer l'estimation du consultant. Il transforme les hypothèses explicites du consultant en une distribution traçable, puis montre **le niveau de risque associé à une décision budgétaire ou de délai**.

## 1. Problème — 1 min

Partir d'une situation familière :

> « Aujourd'hui, on peut avoir un budget de référence auquel on ajoute une marge forfaitaire. Le problème est qu'un +15 % ne dit ni quelle probabilité de dépassement on accepte, ni quels postes justifient cette marge. »

Montrer ensuite que le simulateur travaille avec des hypothèses poste par poste et restitue une distribution plutôt qu'un chiffre unique.

## 2. Entrée Excel — 2 min

Ouvrir le registre utilisé pour la démonstration.

À montrer seulement :

- la feuille `metadata` et la baseline ;
- quelques postes représentatifs dans `risk_register` ;
- une ligne événementielle ;
- la feuille `correlations` si le cas de démonstration l'utilise.

Ne pas passer en revue toutes les colonnes. Insister sur la traçabilité : une hypothèse visible dans Excel doit pouvoir être discutée et corrigée.

## 3. Lancer l'interface — 1 min

Dans Streamlit :

1. charger le classeur ;
2. conserver `10 000` tirages et une seed fixe ;
3. choisir `P90` ;
4. lancer la simulation.

Mentionner que l'interface utilise le même service applicatif que la CLI ; elle n'introduit pas une seconde implémentation du moteur.

## 4. Décision — 3 min

Commencer par les quatre indicateurs :

- P90 ;
- moyenne simulée ;
- probabilité de dépasser la baseline ;
- réserve jusqu'au P90.

Phrase de lecture :

> « Le P90 est le niveau sous lequel tombent environ 90 % des scénarios simulés. La réserve affichée est l'écart entre ce niveau et la baseline, si cet écart est positif. »

Passer ensuite à la S-curve. Montrer qu'on peut lire les deux sens de la décision :

- budget donné → probabilité de ne pas dépasser ;
- probabilité cible → budget correspondant.

Éviter d'appeler le P90 « le bon budget ». Le niveau de confiance dépend de la décision, de l'appétence au risque et du contexte contractuel.

## 5. Priorités de mitigation — 2 min

Ouvrir l'onglet Sensibilité et montrer les trois premiers postes du tornado.

Question à poser au public :

> « Est-ce que ces trois postes correspondent à votre intuition du projet ? Si non, quelle hypothèse devons-nous revoir ? »

Cette question transforme le graphique en outil de validation métier plutôt qu'en résultat décoratif.

Rappeler en une phrase que Spearman mesure une association monotone, pas une causalité.

## 6. Fiabilité numérique — 1 min

Ouvrir l'onglet Convergence. Montrer l'évolution du percentile cible et, s'il existe, le point où le critère automatique détecte une stabilité.

Message :

> « Ce contrôle vérifie que le nombre de tirages est suffisant pour stabiliser le quantile. Il ne garantit pas que les hypothèses saisies sont justes. »

Si une matrice de corrélation est présente, montrer brièvement le diagnostic et rappeler qu'une matrice invalide est refusée plutôt que corrigée silencieusement.

## 7. Export et transmission — 1 min

Ouvrir l'onglet Exports et télécharger le ZIP complet. Expliquer que la restitution conserve les CSV et graphiques issus du même run.

Pour un cas réel, conserver aussi :

- la version / le commit du moteur ;
- la seed ;
- le nombre de tirages ;
- le registre autorisé ou son identifiant interne ;
- les décisions prises lors de la revue.

## Questions probables

### « Pourquoi 10 000 tirages ? »

C'est un point de départ pratique, mais le diagnostic de convergence est plus pertinent qu'un nombre magique. Selon la forme de la distribution et le percentile étudié, il peut falloir plus ou moins de tirages.

### « Pourquoi P80 ou P90 plutôt qu'une marge de 15 % ? »

Parce qu'un percentile relie directement le montant à un niveau de confiance issu des hypothèses du registre. Une marge forfaitaire ne fournit pas cette information.

### « Si le P90 est dépassé dans la réalité, le modèle est faux ? »

Pas nécessairement. Un événement peu probable peut se produire. Le modèle doit être jugé sur la qualité et la calibration de ses hypothèses sur plusieurs cas, pas sur un seul résultat réalisé.

### « Peut-on corriger automatiquement une matrice de corrélation ? »

Techniquement oui, mais la version actuelle ne le fait volontairement pas : une réparation silencieuse modifierait une hypothèse métier. Le diagnostic sert à corriger explicitement la matrice.

### « Peut-on tester une mitigation ? »

C'est l'extension prioritaire des semaines 5–6 : mode what-if et comparaison de scénarios base / mitigé.

## Critère de réussite de la restitution

À la fin, une personne non mathématicienne doit être capable d'expliquer :

1. ce que représente P90 ;
2. ce que signifie la probabilité de dépassement de la baseline ;
3. quel poste apparaît comme le plus sensible ;
4. pourquoi la convergence numérique ne remplace pas la validation des hypothèses ;
5. comment récupérer le pack d'artefacts du run.

Le cas synthétique du dépôt peut démontrer le fonctionnement. Il ne doit jamais être présenté comme une validation terrain réelle.
