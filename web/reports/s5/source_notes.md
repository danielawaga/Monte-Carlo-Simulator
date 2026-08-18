# Notes de construction — rapport S5

## Job de reporting

- Question : présenter de manière professionnelle ce qui a été réalisé pendant la S5 et pourquoi ces réalisations sont utiles.
- Audience : parties prenantes produit, encadrant de stage et responsables projet.
- Période : 10–17 août 2026, avec validation technique et captures effectuées le 18 août 2026.
- Référence : état S4 décrit dans la note de rapport de stage et historique Git S5.
- Critère de réussite : le lecteur doit comprendre le passage d’un démonstrateur utilisable à un poste de décision structuré, les preuves de qualité et les limites restantes.

## Correspondance avec la structure exécutive requise

1. Titre : « Rapport S5 — Interface et workflow décisionnel ».
2. Executive Summary : synthèse en trois points.
3. Conclusions principales et preuves visuelles : progression, pilotage, configuration, résultats et scénarios.
4. Prochaines étapes : intégration backend, persistance, validation terrain et passation.
5. Questions ouvertes : protocole d’approbation, conservation des scénarios et métriques d’usage.
6. Limites et hypothèses : données de démonstration, captures postérieures à la clôture S5 et absence de validation sur données client.

## Carte des visuels

| Section | Question | Forme | Preuve | Palette | Implication |
| --- | --- | --- | --- | --- | --- |
| Pilotage | L’interface hiérarchise-t-elle la décision ? | Capture plein écran | `01_tableau_de_bord.png` | Interface RiskSim bleu/orange | Les indicateurs et décisions sont visibles avant le détail. |
| Configuration | Les hypothèses sont-elles explicites et éditables ? | Capture d’écran | `02_configuration.png` | Interface RiskSim bleu/orange | La traçabilité est intégrée au parcours. |
| Résultats | Les distributions et percentiles sont-ils lisibles ? | Capture d’écran | `03_resultats.png` | Courbes orange, repères bleu/gris | La restitution relie distribution, seuils et sensibilité. |
| Scénarios | Le workflow permet-il un raisonnement what-if ? | Capture d’écran | `04_comparaison_scenarios.png` | Référence bleue, mitigation verte | Les écarts P80/P90 deviennent directement comparables. |

Les captures sont utilisées comme preuves d’interface, pas comme source de validation statistique. Chaque visuel est placé après un paragraphe expliquant le message et l’implication.

## Omissions et précautions

- Aucun graphique temporel de progression n’a été construit : les preuves disponibles sont des jalons Git discrets, pas une série temporelle assez dense.
- Les chiffres de démonstration de l’interface ne doivent pas être présentés comme des résultats client.
- Les 359 tests valident le logiciel ; ils ne mesurent pas la précision prédictive du modèle.
