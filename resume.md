# Transmission de contexte — RiskSim / Monte-Carlo Simulator

Ce fichier permet de reprendre le travail dans une nouvelle conversation sans
reconstituer tout l'historique.

## Dernière mise à jour — paquet portable à un seul EXE

La stratégie à un seul exécutable console est désormais **implémentée et
validée**. Le nouveau ZIP contient uniquement :

```text
RiskSim-Portable/
├── RiskSim.exe
├── LISEZ-MOI.txt
└── _internal/
```

`RiskSim-Diagnostic.exe` et `Fermer-RiskSim.exe` ont été retirés. Le terminal
de `RiskSim.exe` affiche le démarrage et les erreurs ; l'arrêt fonctionne avec
`exit`, `quit`, `q` ou le bouton « Quitter RiskSim ». `Ctrl+C` reste pris en
charge nativement par Uvicorn dans une console Windows normale.

Nouveau ZIP : `output/packages/RiskSim-Windows-x64-Portable.zip`

- taille : 122 069 970 octets ;
- SHA-256 : `8F2E56B26896C3899F1D16CD3D809DDE4D9EECAF9148656E8873A2FC510C8B20` ;
- 1 936 entrées, dont un seul fichier `.exe`.

Validations finales : 416 tests Python, 14 tests React, construction React,
simulation depuis le dossier construit et depuis le ZIP réextrait, arrêt via
le terminal et l'interface, seconde instance, puis déplacement du dossier
après arrêt. Tous ces contrôles ont réussi.

## Projet et objectif

**RiskSim — Monte Carlo** est une plateforme locale de simulation Monte-Carlo
pour l'analyse des risques de **coût** ou de **durée** d'un projet. L'objectif
est de permettre à un consultant de :

1. créer ou importer un registre de risques Excel ;
2. définir les postes et leurs distributions probabilistes ;
3. définir des corrélations lorsque les postes ne sont pas indépendants ;
4. configurer puis lancer une simulation ;
5. lire, sauvegarder et exporter les résultats (Excel, ZIP de graphiques).

Le projet est dans :

`C:\Users\PC\Documents\Dossier Etudes\ECC\Stage opérateur\Monte-Carlo-Simulator`

Le dépôt distant est :

`https://github.com/danielawaga/Monte-Carlo-Simulator`

## Architecture actuelle

| Couche | Technologie / emplacement | Rôle |
| --- | --- | --- |
| Interface | React + TypeScript, `web/` | Interface RiskSim : accueil, registre, simulation, résultats, paramètres. |
| API | FastAPI, `src/monte_carlo_simulator/web_api.py` | Sert l'interface construite et expose les routes de registre, simulation, export et stockage local. |
| Moteur | Python, `src/monte_carlo_simulator/` | Validation, distributions, échantillonnage, corrélations et calcul des percentiles. |
| Persistance | SQLite locale | Enregistre les projets, simulations et scénarios sur le poste. |
| Portabilité Windows | PyInstaller, `packaging/` | Produit une version Windows x64 sans Python, Node.js ni packages à installer. |

Le navigateur ne fait qu'afficher l'interface. Le moteur tourne localement sur
`127.0.0.1` : aucune donnée n'est exposée sur le réseau.

## Fonctionnalités interface déjà réalisées

- Panneau latéral avec Accueil, Registre de risques, Simulation, Résultats et
  Paramètres ; thèmes clair, sombre et système.
- Registre de risques organisé en cinq étapes sur une même ligne : Projet,
  Postes, Corrélations, Validation, Enregistrés.
- Initialisation guidée : **Créer un nouveau projet** ou **Importer Excel**.
- Saisie des données du projet, des postes et de leurs distributions ; matrice
  de corrélation ; validations métier et indications lorsque l'étape suivante
  est bloquée.
- Page Simulation : aperçu de projet, choix du nombre de tirages, graine,
  niveaux P50/P75/P80/P90/P95, seuil de dépassement et scénario documenté.
- Page Résultats : synthèse, histogramme, S-curve, sensibilité, robustesse,
  exports Excel, dossier ZIP des graphiques et conservation dans l'historique.
- Création du rapport de semaine 6 en PDF ; les documents de référence ont été
  enrichis dans `docs/reference/`.

## État Git à la dernière vérification

Branche locale courante : `main`.

Des modifications **locales non commitées** existent et concernent la version
portable. Elles doivent être vérifiées, puis ajoutées dans un commit séparé.

Fichiers modifiés :

- `src/monte_carlo_simulator/launcher.py`
- `src/monte_carlo_simulator/web_api.py`
- `tests/unit/test_launcher.py`
- `tests/unit/test_web_api.py`
- `web/src/components/navigation/Sidebar.tsx`
- `web/src/styles/enhancements.css`

Nouveaux fichiers utiles non suivis :

- `packaging/monte-carlo-simulator-portable.spec`
- `packaging/RiskSim-Portable-LISEZ-MOI.txt`
- `web/src/components/navigation/Sidebar.test.tsx`
- `output/packages/RiskSim-Windows-x64-Portable.zip` (artefact livré ; ne pas
  ajouter aveuglément tout `output/` car il contient d'autres fichiers)

Fichiers/dossiers non liés, à préserver et à ne pas ajouter au commit sans
demande explicite :

- `codex-command-runner.exe`
- `codex-windows-sandbox-setup.exe`
- `public/`
- `tmp/`

## Portabilité Windows — travail récent

Une distribution PyInstaller **onedir** a été construite. Elle contient un
dossier `_internal` avec l'interpréteur Python et toutes les dépendances.
L'utilisateur n'a donc rien à installer sur une machine Windows x64.

Le ZIP produit est :

`output/packages/RiskSim-Windows-x64-Portable.zip`

Ancienne empreinte SHA-256 (version remplacée) :

`770E46565FFDE898E372253E5E6D85E225E05DB999CB997FB9D1BE57F3ADF56B`

Le ZIP a été validé sur une machine virtuelle Windows : une simulation et les
modifications de registre ont fonctionné sans installation préalable.

### Incident observé après extraction sur le Bureau

L'utilisateur a signalé un échec de `Fermer-RiskSim.exe`. Le journal était :

```text
RuntimeError: RiskSim n'a pas répondu à la demande d'arrêt.
```

Analyse effectuée :

- le dossier extrait contenait un `RiskSim.exe` plus ancien (horodaté 05:37)
  et un `Fermer-RiskSim.exe` / `RiskSim-Diagnostic.exe` plus récents
  (horodatés 06:27) ;
- deux processus `RiskSim.exe` issus de ce dossier étaient actifs ;
- l'ancien lanceur ne connaissait pas complètement le nouveau mécanisme
  d'arrêt, ce qui explique l'échec du programme de fermeture ;
- l'alerte affichée parlait à tort de « démarrage » parce que le gestionnaire
  d'erreur est commun aux lanceurs.

Ce comportement ne correspond pas à un virus ni à des dépendances manquantes :
il s'agit d'un paquet mélangeant deux versions.

### Décision appliquée dans la dernière itération

La distribution a été simplifiée à **un seul exécutable console**, `RiskSim.exe` :

1. l'utilisateur double-clique sur `RiskSim.exe` ;
2. un terminal reste visible, décrit le démarrage et affiche les erreurs ;
3. le navigateur s'ouvre après disponibilité effective du serveur ;
4. `Ctrl+C` arrête proprement l'application ;
5. une petite boucle de commandes accepte aussi `exit`, `quit` et `q` ;
6. le bouton « Quitter RiskSim » de l'interface peut être conservé ;
7. `RiskSim-Diagnostic.exe` et `Fermer-RiskSim.exe` sont supprimés.

Le dossier `_internal` restera nécessaire. Un unique fichier `.exe` autonome
est possible avec PyInstaller en mode *onefile*, mais est moins fiable pour ce
projet (démarrage plus lent, extraction temporaire, diagnostic plus difficile).
La meilleure livraison est donc : **un seul EXE visible + `_internal`**, dans
un seul ZIP.

## Modifications portables déjà présentes dans le code local

Le lanceur actuel comporte déjà les éléments suivants :

- sélection d'un port local libre ;
- attente de disponibilité avant ouverture du navigateur ;
- prévention d'instances concurrentes par mutex Windows ;
- journal de démarrage `RiskSim-erreur-demarrage.txt` ;
- endpoint FastAPI `POST /api/shutdown` ;
- bouton « Quitter RiskSim » dans la barre latérale ;
- tests ciblés du lanceur, de l'API et du composant Sidebar.

La stratégie à trois EXE a été remplacée et le ZIP a été reconstruit depuis une
sortie PyInstaller propre afin d'éviter tout mélange de versions.

## Vérifications déjà réussies

- lint Python : réussi ;
- tests unitaires Python ciblés : réussis ;
- tests React : réussis ;
- construction production React : réussie ;
- simulation empaquetée : réussie (projet de test, 1 000 tirages) ;
- essai du cycle démarrage / seconde instance / arrêt : réussi depuis une
construction cohérente et depuis le ZIP extrait.

## Instructions de reprise proposées

Dans une nouvelle conversation, transmettre ce fichier et demander par exemple :

> Reprends le projet RiskSim en suivant `resume.md`. La distribution portable
> à un seul `RiskSim.exe` est construite et validée. Commence par vérifier
> l'état Git et conserve les fichiers non liés avant toute nouvelle évolution.

Avant une nouvelle construction, vérifier qu'aucun `RiskSim.exe` n'est encore
actif dans le Gestionnaire des tâches ou arrêter l'application avec `Ctrl+C`.
