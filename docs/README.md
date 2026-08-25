# Documentation

Les documents sont rangés par nature, pas par date : ce qui doit rester à jour est séparé de ce qui
fige un état livré.

## `guides/` — utiliser et reprendre le projet

Documentation opérationnelle, maintenue à jour avec le code.

| Document | Pour qui | Contenu |
| --- | --- | --- |
| [`user_guide_30min.md`](guides/user_guide_30min.md) | consultant | prise en main complète : installation, registre, simulation, lecture, export |
| [`user_guide.md`](guides/user_guide.md) | consultant, intégrateur | référence du schéma Excel `1.0`, règles de validation et chemins d'exécution |
| [`handover.md`](guides/handover.md) | repreneur technique | passation : architecture, installation, points d'extension, diagnostic |

## `reference/` — comprendre les choix

Documentation de fond, maintenue à jour avec le moteur.

| Document | Contenu |
| --- | --- |
| [`project_overview.md`](reference/project_overview.md) | vue d'ensemble fonctionnelle, parcours utilisateur, résultats, exécution et limites |
| [`architecture.md`](reference/architecture.md) | architecture technique détaillée : React, API, moteur, Excel, SQLite, sécurité et packaging |
| [`methodology.md`](reference/methodology.md) | choix techniques et invariants du moteur |
| [`methodology_note.md`](reference/methodology_note.md) | même méthode, sans prérequis mathématique |
| [`registre_synthetique_batiment.md`](reference/registre_synthetique_batiment.md) | cas d'étude documenté servant de support de validation |

## `validation/` — preuves publiées

Résultats tabulaires des contrôles de distributions, de corrélations et de registres invalides,
au format CSV et JSON. Ces fichiers sont des données, pas de la prose.

## `archive/` — livrables datés

Documents qui rendent compte d'un périmètre à une date donnée. **Ils ne sont pas mis à jour** : les
corriger falsifierait ce qu'ils attestent. Ils peuvent donc décrire des choses qui ont changé depuis,
comme l'interface Streamlit retirée en S6.

| Document | Date de référence |
| --- | --- |
| [`s4_restitution.md`](archive/s4_restitution.md) | trame de restitution orale S4 |
| [`consultant_validation_workshop.md`](archive/consultant_validation_workshop.md) | atelier de validation consultant, semaine 3 |
| [`notes_conversation_rapport_stage.md`](archive/notes_conversation_rapport_stage.md) | notes préparatoires au rapport de stage |

## Ailleurs dans le dépôt

- [`../README.md`](../README.md) — présentation générale, installation et architecture ;
- [`../web/README.md`](../web/README.md) — notes sur l'interface React ;
- [`../reports/`](../reports/) — livrables générés (rapport S5, étude de cas PDF) ;
- [`../scripts/case_study/README.md`](../scripts/case_study/README.md) — chaîne de génération de l'étude de cas.
