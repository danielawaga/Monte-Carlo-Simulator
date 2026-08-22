import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const reportDir = dirname(fileURLToPath(import.meta.url));
const generatedAt = '2026-08-18T01:30:00+01:00';

const sources = [
  { id: 's5_scope', label: 'Périmètre S5 vérifié dans le dépôt', path: 'evidence/s5_scope.md', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Représentation structurée des trois couches définies dans le périmètre S5.', sql: "SELECT * FROM (VALUES (1, 'Présentation', 'Navigation, formulaires, tableaux et graphiques', 'React · TypeScript · Vite'), (2, 'Adaptation', 'Validation des requêtes et sérialisation des résultats', 'Service HTTP / contrat JSON à finaliser'), (3, 'Domaine', 'Simulation, distributions, corrélations et analyses', 'Python · NumPy · pandas · SciPy')) AS t(ordre, couche, responsabilite, technologies)" } },
  { id: 'git_history', label: 'Historique Git S5 — 15 au 17 août 2026', path: 'evidence/s5_git_history.md', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Synthèse des réalisations attestées par les commits S5 non fusion.', filters: ['Commits non fusion du 10 au 17 août 2026'], sql: "SELECT * FROM (VALUES (1, 'Interface consultant', 'Parcours Streamlit renforcé et export Excel amélioré', 'Réduit les manipulations hors outil', 'Terminé'), (2, 'Hypothèses', 'Édition, ajout, suppression et réinitialisation après import', 'Permet un what-if contrôlé', 'Terminé'), (3, 'Frontend', 'Socle React, TypeScript et Vite', 'Sépare présentation et domaine', 'Terminé'), (4, 'Restitution', 'Histogramme, S-curve et valeurs exactes interactives', 'Améliore l’interprétation', 'Terminé'), (5, 'Scénarios', 'Comparaison Référence / Mitigation', 'Structure le raisonnement what-if', 'Terminé'), (6, 'Gouvernance', 'Navigation, pilotage, registre, paramètres et administration', 'Prépare un usage d’équipe', 'Consolidé')) AS t(ordre, axe, realisation, valeur, statut)" } },
  { id: 'app_routes', label: 'Routes de l’interface RiskSim', path: 'evidence/app_routes.md', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Comptage des routes fonctionnelles déclarées dans web/src/App.tsx, hors redirection générique.', metric_definitions: ['Sections navigables = nombre de routes métier uniques, accueil inclus et redirection générique exclue.'], sql: 'SELECT 9 AS routes' } },
  { id: 'validation', label: 'Résultats des contrôles Python, Vite et Chromium', path: 'evidence/validation.md', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Contrôles techniques exécutés le 18 août 2026.', metric_definitions: ['Tests réussis = nombre de cas pytest terminés avec succès dans la suite complète.'], sql: "SELECT * FROM (VALUES (1, 'Tests Python', '359 / 359 réussis', 'Le socle métier et les workflows testés sont stables.'), (2, 'Build frontend', 'Réussi · 1 593 modules', 'TypeScript et Vite produisent une version de production.'), (3, 'Vérification Chromium', '4 vues contrôlées', 'Les écrans illustrés se chargent sans overlay d’erreur.'), (4, 'Reproductibilité', 'Graine 20260816', 'Le scénario de démonstration peut être rejoué à hypothèses constantes.')) AS t(ordre, controle, resultat, lecture)" } },
  { id: 'test_count', label: 'Comptage pytest du 18 août 2026', path: 'evidence/validation.md', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Nombre de tests terminés avec succès dans la suite complète.', metric_definitions: ['Tests automatisés réussis = nombre de cas pytest dont toutes les assertions sont passées.'], sql: 'SELECT 359 AS tests' } },
  { id: 'dashboard_capture', label: 'Capture — tableau de bord RiskSim', path: 'images/01_tableau_de_bord.png' },
  { id: 'configuration_capture', label: 'Capture — configuration et hypothèses', path: 'images/02_configuration.png', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Paramètres visibles dans la configuration de démonstration.', metric_definitions: ['Itérations = nombre de tirages Monte Carlo configurés.', 'Niveaux de confiance = P50, P80, P90 et P95.'], sql: 'SELECT 50000 AS iterations, 4 AS levels' } },
  { id: 'results_capture', label: 'Capture — résultats probabilistes', path: 'images/03_resultats.png' },
  { id: 'scenarios_capture', label: 'Capture — comparaison de scénarios', path: 'images/04_comparaison_scenarios.png', query: { engine: 'duckdb', language: 'sql', executed_at: generatedAt, description: 'Valeurs de démonstration affichées dans la comparaison Référence / Mitigation.', filters: ['Jeu de démonstration Projet Atlas', '50 000 itérations par scénario'], metric_definitions: ['Variation vs référence = (montant mitigation - montant référence) / montant référence.'], sql: "SELECT * FROM (VALUES ('P80', 'Référence', 4.12, 0.00), ('P80', 'Mitigation', 3.55, -0.14), ('P90', 'Référence', 6.24, 0.00), ('P90', 'Mitigation', 5.10, -0.18), ('Réserve P80', 'Référence', 2.02, 0.00), ('Réserve P80', 'Mitigation', 1.45, -0.28)) AS t(indicateur, scenario, montant_m_eur, variation_pct)" } },
];

function imageBlock(fileName, alt, caption) {
  const data = readFileSync(join(reportDir, 'images', fileName)).toString('base64');
  return `<figure style="margin:0;font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#14213d"><img src="data:image/png;base64,${data}" alt="${alt}" style="display:block;width:100%;height:auto;border:1px solid #dce3ec;border-radius:14px;background:#f8fafc"><figcaption style="padding:12px 2px 2px;color:#667085;font-size:12px;line-height:1.5">${caption}</figcaption></figure>`;
}

const artifact = {
  surface: 'report',
  manifest: {
    version: 1,
    surface: 'report',
    title: 'Rapport S5 — Interface et workflow décisionnel',
    description: 'Bilan du 10 au 17 août 2026 · Monte-Carlo-Simulator',
    generatedAt,
    cards: [
      { id: 'routes_card', description: 'Accueil, registre, simulation, résultats, gouvernance et compte.', dataset: 'routes_summary', sourceId: 'app_routes', metrics: [{ label: 'Sections navigables', field: 'routes', format: 'number' }] },
      { id: 'tests_card', description: 'Suite Python exécutée sur l’état final du dépôt.', dataset: 'tests_summary', sourceId: 'test_count', metrics: [{ label: 'Tests automatisés réussis', field: 'tests', format: 'number' }] },
      { id: 'iterations_card', description: 'Valeur par défaut retenue pour la démonstration et le reporting.', dataset: 'simulation_summary', sourceId: 'configuration_capture', metrics: [{ label: 'Itérations par simulation', field: 'iterations', format: 'compact' }] },
      { id: 'levels_card', description: 'P50, P80, P90 et P95 sont préparés dans le parcours.', dataset: 'levels_summary', sourceId: 'configuration_capture', metrics: [{ label: 'Niveaux de confiance', field: 'levels', format: 'number' }] },
    ],
    charts: [
      {
        id: 'scenario_chart',
        title: 'Percentiles et réserve par scénario',
        subtitle: 'Référence et mitigation · montants en millions d’euros · 50 000 itérations par scénario.',
        showDescription: true,
        intent: 'comparison',
        question: 'Quel scénario réduit le plus les niveaux d’engagement et la réserve associée ?',
        rationale: 'Un graphique en barres groupées compare deux scénarios sur trois indicateurs de même unité sans suggérer une continuité temporelle.',
        comparisonContext: { baseline: 'Scénario Référence', denominator: '50 000 itérations par scénario', grain: 'Indicateur × scénario', semanticFamily: 'Percentiles et réserve du coût total', unit: 'M€' },
        type: 'bar',
        dataset: 'scenario_comparison',
        sourceId: 'scenarios_capture',
        valueFormat: 'number',
        unit: 'M€',
        layout: 'full',
        encodings: {
          x: { field: 'indicateur', type: 'ordinal', label: 'Indicateur' },
          y: { field: 'montant_m_eur', type: 'quantitative', label: 'Montant', format: 'number', unit: 'M€' },
          color: { field: 'scenario', type: 'nominal', label: 'Scénario' },
          tooltip: [{ field: 'variation_pct', type: 'quantitative', label: 'Variation vs référence', format: 'percent' }],
        },
      },
    ],
    tables: [
      {
        id: 'delivery_table',
        title: 'Réalisations du S5',
        subtitle: 'Jalons attestés entre le 15 et le 17 août 2026.',
        showDescription: true,
        dataset: 'delivery_items',
        sourceId: 'git_history',
        defaultSort: { field: 'ordre', direction: 'asc' },
        density: 'spacious',
        layout: 'full',
        columns: [
          { field: 'ordre', label: '#', format: 'number' },
          { field: 'axe', label: 'Axe', type: 'text' },
          { field: 'realisation', label: 'Réalisation', type: 'text' },
          { field: 'valeur', label: 'Valeur apportée', type: 'text' },
          { field: 'statut', label: 'Statut', type: 'text' },
        ],
      },
      {
        id: 'architecture_table',
        title: 'Séparation des responsabilités',
        subtitle: 'Architecture cible définie pendant le S5.',
        showDescription: true,
        dataset: 'architecture_layers',
        sourceId: 's5_scope',
        defaultSort: { field: 'ordre', direction: 'asc' },
        density: 'spacious',
        layout: 'full',
        columns: [
          { field: 'ordre', label: 'Niveau', format: 'number' },
          { field: 'couche', label: 'Couche', type: 'text' },
          { field: 'responsabilite', label: 'Responsabilité', type: 'text' },
          { field: 'technologies', label: 'Technologies / composants', type: 'text' },
        ],
      },
      {
        id: 'validation_table',
        title: 'Contrôles de qualité',
        subtitle: 'État vérifié le 18 août 2026.',
        showDescription: true,
        dataset: 'validation_checks',
        sourceId: 'validation',
        defaultSort: { field: 'ordre', direction: 'asc' },
        density: 'spacious',
        layout: 'full',
        columns: [
          { field: 'ordre', label: '#', format: 'number' },
          { field: 'controle', label: 'Contrôle', type: 'text' },
          { field: 'resultat', label: 'Résultat', type: 'text' },
          { field: 'lecture', label: 'Interprétation', type: 'text' },
        ],
      },
    ],
    sources,
    blocks: [
      { id: 'title', type: 'markdown', body: '# Rapport S5 — Interface et workflow décisionnel' },
      {
        id: 'executive_summary',
        type: 'markdown',
        body: '## Executive Summary\n\n- **Le S5 a transformé l’interface en véritable poste de décision.** Le parcours ne se limite plus au lancement d’une simulation : il structure désormais le pilotage, les hypothèses, les résultats et la comparaison de scénarios.\n- **La restitution est devenue interactive et traçable.** Les percentiles, distributions, facteurs de sensibilité et hypothèses sont présentés dans un parcours cohérent, avec des valeurs exactes accessibles dans les graphiques.\n- **L’état livré est techniquement solide, mais l’intégration doit encore être finalisée.** Les 359 tests Python passent et le frontend compile en production ; la persistance des scénarios et la connexion complète React–Python restent les priorités du S6.',
      },
      { id: 'headline_metrics', type: 'metric-strip', cardIds: ['routes_card', 'tests_card', 'iterations_card', 'levels_card'] },
      {
        id: 'progress_section',
        type: 'markdown',
        sourceId: 's5_scope',
        body: '## Le S5 a transformé un démonstrateur en poste de décision\n\n**La semaine de marge prévue pour les retours et extensions a été utilisée pour industrialiser l’expérience utilisateur.** L’interface Streamlit a d’abord été renforcée pour permettre l’édition des hypothèses et améliorer les exports. Une interface React, TypeScript et Vite a ensuite été créée pour séparer plus nettement la présentation du moteur probabiliste.\n\nCette progression répond à un besoin concret : un consultant ou un responsable projet doit comprendre la position budgétaire, vérifier les hypothèses et comparer les options sans parcourir une succession de widgets techniques. Le S5 apporte donc moins de nouveaux calculs que de capacité à expliquer, gouverner et réutiliser les calculs existants.',
      },
      { id: 'delivery_table_block', type: 'table', tableId: 'delivery_table' },
      {
        id: 'dashboard_section',
        type: 'markdown',
        sourceId: 'app_routes',
        body: '## Le pilotage place la décision avant le détail\n\n**Le tableau de bord présente immédiatement le budget de référence, la moyenne simulée, la réserve P80 et les risques prioritaires.** Les échéances et décisions attendues apparaissent sur la même vue, ce qui transforme les sorties Monte Carlo en objets de gouvernance.\n\nLa lecture attendue est simple : identifier l’écart au budget, repérer les domaines exposés, puis ouvrir le registre ou l’analyse détaillée. Cette hiérarchie évite de commencer par les paramètres mathématiques lorsque la question du lecteur est d’abord décisionnelle.',
      },
      { id: 'dashboard_image', type: 'html', sourceId: 'dashboard_capture', body: imageBlock('01_tableau_de_bord.png', 'Tableau de bord RiskSim présentant les indicateurs budgétaires, les domaines de risque et les décisions à venir.', 'Figure 1 — Vue de pilotage du portefeuille de risques. Capture réalisée le 18 août 2026 sur les données de démonstration du Projet Atlas.') },
      {
        id: 'configuration_section',
        type: 'markdown',
        sourceId: 'configuration_capture',
        body: '## Les hypothèses deviennent visibles, modifiables et réutilisables\n\n**La configuration réunit le registre Excel, le nombre de simulations, la graine reproductible, les niveaux de confiance et les hypothèses métier.** Les trois hypothèses affichées — inflation, indépendance des risques et horizon d’analyse — peuvent être complétées, modifiées ou supprimées avant l’exécution.\n\nL’apport principal est la traçabilité : le résultat peut être relié à un fichier, une graine et des hypothèses explicites. Cela réduit le risque d’un chiffre produit sans contexte et prépare la comparaison de scénarios sur une base contrôlée.',
      },
      { id: 'configuration_image', type: 'html', sourceId: 'configuration_capture', body: imageBlock('02_configuration.png', 'Écran de configuration RiskSim montrant l’import Excel, la graine, les niveaux de confiance et les hypothèses modifiables.', 'Figure 2 — Configuration de la simulation et documentation des hypothèses. La graine 20260816 rend le scénario de démonstration reproductible.') },
      {
        id: 'architecture_section',
        type: 'markdown',
        sourceId: 's5_scope',
        body: '## La séparation technique protège la logique probabiliste\n\n**Le frontend n’a pas vocation à recalculer les distributions.** React porte la présentation et les interactions ; la couche d’adaptation doit traduire les requêtes ; le moteur Python conserve les distributions, corrélations, percentiles, analyses de sensibilité et exports.\n\nCette séparation limite les divergences entre interfaces et rend possible une évolution de l’expérience utilisateur sans modifier les règles mathématiques validées.',
      },
      { id: 'architecture_table_block', type: 'table', tableId: 'architecture_table' },
      {
        id: 'results_section',
        type: 'markdown',
        sourceId: 'results_capture',
        body: '## Les résultats relient distribution, seuils et facteurs d’exposition\n\n**La page de résultats combine une synthèse exécutive et des éléments d’analyse.** La moyenne, P80, P90 et la probabilité de dépassement sont visibles avant l’histogramme. La S-curve permet ensuite de lire la probabilité cumulée, tandis que le classement de Spearman oriente l’action vers les risques les plus influents.\n\nDans le jeu de démonstration, le budget de référence est de 2,10 M€, la moyenne simulée de 2,45 M€ et le P80 de 4,12 M€. Ces valeurs illustrent le workflow ; elles ne constituent pas une estimation client.',
      },
      { id: 'results_image', type: 'html', sourceId: 'results_capture', body: imageBlock('03_resultats.png', 'Page de résultats RiskSim avec indicateurs, histogramme, S-curve et classement de sensibilité.', 'Figure 3 — Restitution probabiliste : distribution des coûts, niveaux P80/P90 et principaux risques par sensibilité.') },
      {
        id: 'scenarios_section',
        type: 'markdown',
        sourceId: 'scenarios_capture',
        body: '## La comparaison de scénarios rend le what-if exploitable\n\n**Le scénario de mitigation est comparé à une référence validée sur les mêmes indicateurs.** Dans la démonstration, le P80 passe de 4,12 M€ à 3,55 M€ et le P90 de 6,24 M€ à 5,10 M€. La courbe cumulée met en évidence l’amélioration sur l’ensemble de la distribution, pas seulement sur un chiffre isolé.\n\nCette vue prépare une discussion structurée : quelles mesures expliquent l’écart, qui doit approuver le scénario et quelle réserve doit être retenue ? La comparaison reste un outil d’aide à la décision, pas une recommandation automatique.',
      },
      { id: 'scenario_chart_block', type: 'chart', chartId: 'scenario_chart' },
      {
        id: 'scenarios_capture_note',
        type: 'markdown',
        body: '**La capture suivante montre comment cette comparaison quantitative s’intègre dans le parcours utilisateur.** Les cartes P80/P90, la courbe cumulée et la synthèse comparative restent visibles dans une même lecture.',
      },
      { id: 'scenarios_image', type: 'html', sourceId: 'scenarios_capture', body: imageBlock('04_comparaison_scenarios.png', 'Comparaison RiskSim des scénarios Référence et Mitigation avec P80, P90, réserve et courbes cumulées.', 'Figure 4 — Comparaison Référence / Mitigation. Les valeurs sont issues du jeu de démonstration et servent à illustrer le raisonnement what-if.') },
      {
        id: 'quality_section',
        type: 'markdown',
        sourceId: 'validation',
        body: '## Les contrôles confirment la stabilité logicielle\n\n**La suite Python compte 359 tests réussis et la compilation de production du frontend est valide.** Les quatre vues illustrées ont également été contrôlées dans Chromium sans page blanche ni overlay d’erreur.\n\nCes éléments montrent que l’évolution S5 n’a pas dégradé le socle logiciel. Ils ne prouvent toutefois ni la qualité des hypothèses métier ni la précision prédictive sur un projet réel.',
      },
      { id: 'validation_table_block', type: 'table', tableId: 'validation_table' },
      {
        id: 'next_steps',
        type: 'markdown',
        body: '## Priorités recommandées pour le S6\n\n1. **Connecter le frontend React au service Python** en conservant une couche d’adaptation mince et un contrat JSON versionné.\n2. **Persister les scénarios et leur statut d’approbation** afin de retrouver l’historique après rechargement et d’éviter les comparaisons non traçables.\n3. **Préserver les matrices de corrélation dans le workflow éditable** et ajouter un contrôle de non-régression dédié.\n4. **Réaliser une validation métier encadrée** avec un registre anonymisé et autorisé, puis documenter les écarts entre attentes et usage réel.\n5. **Finaliser la passation** avec les procédures de déploiement, de sauvegarde, d’administration et de traitement des incidents.',
      },
      {
        id: 'questions',
        type: 'markdown',
        body: '## Questions à trancher\n\n- Quel rôle peut valider définitivement un scénario et rendre ses résultats visibles dans le reporting exécutif ?\n- Quelle durée de conservation appliquer aux registres, hypothèses, graines et exports ?\n- Faut-il permettre l’édition directe de toutes les distributions dans React ou conserver Excel comme source métier principale ?\n- Quels indicateurs d’usage permettront de vérifier que les consultants comprennent réellement P80, P90 et la sensibilité ?',
      },
      {
        id: 'caveats',
        type: 'markdown',
        body: '## Limites et hypothèses\n\n- Les captures du 18 août illustrent l’état consolidé immédiatement après le S5 ; certaines finitions visuelles sont postérieures aux commits S5 du 17 août.\n- Les montants et risques du Projet Atlas sont fictifs et servent uniquement à démontrer le parcours.\n- Les 359 tests mesurent la couverture fonctionnelle du logiciel, pas la fiabilité d’une prévision métier.\n- La validation sur un registre client réel et autorisé n’est pas encore attestée.\n- La connexion complète entre l’interface React et le moteur Python reste à finaliser.',
      },
    ],
  },
  snapshot: {
    version: 1,
    generatedAt,
    status: 'ready',
    datasets: {
      routes_summary: [{ routes: 9 }],
      tests_summary: [{ tests: 359 }],
      simulation_summary: [{ iterations: 50000 }],
      levels_summary: [{ levels: 4 }],
      scenario_comparison: [
        { indicateur: 'P80', scenario: 'Référence', montant_m_eur: 4.12, variation_pct: 0 },
        { indicateur: 'P80', scenario: 'Mitigation', montant_m_eur: 3.55, variation_pct: -0.14 },
        { indicateur: 'P90', scenario: 'Référence', montant_m_eur: 6.24, variation_pct: 0 },
        { indicateur: 'P90', scenario: 'Mitigation', montant_m_eur: 5.10, variation_pct: -0.18 },
        { indicateur: 'Réserve P80', scenario: 'Référence', montant_m_eur: 2.02, variation_pct: 0 },
        { indicateur: 'Réserve P80', scenario: 'Mitigation', montant_m_eur: 1.45, variation_pct: -0.28 },
      ],
      delivery_items: [
        { ordre: 1, axe: 'Interface consultant', realisation: 'Parcours Streamlit renforcé et export Excel amélioré', valeur: 'Réduit les manipulations hors outil', statut: 'Terminé' },
        { ordre: 2, axe: 'Hypothèses', realisation: 'Édition, ajout, suppression et réinitialisation après import', valeur: 'Permet un what-if contrôlé', statut: 'Terminé' },
        { ordre: 3, axe: 'Frontend', realisation: 'Socle React, TypeScript et Vite', valeur: 'Sépare présentation et domaine', statut: 'Terminé' },
        { ordre: 4, axe: 'Restitution', realisation: 'Histogramme, S-curve et valeurs exactes interactives', valeur: 'Améliore l’interprétation', statut: 'Terminé' },
        { ordre: 5, axe: 'Scénarios', realisation: 'Comparaison Référence / Mitigation', valeur: 'Structure le raisonnement what-if', statut: 'Terminé' },
        { ordre: 6, axe: 'Gouvernance', realisation: 'Navigation, pilotage, registre, paramètres et administration', valeur: 'Prépare un usage d’équipe', statut: 'Consolidé' },
      ],
      architecture_layers: [
        { ordre: 1, couche: 'Présentation', responsabilite: 'Navigation, formulaires, tableaux et graphiques', technologies: 'React · TypeScript · Vite' },
        { ordre: 2, couche: 'Adaptation', responsabilite: 'Validation des requêtes et sérialisation des résultats', technologies: 'Service HTTP / contrat JSON à finaliser' },
        { ordre: 3, couche: 'Domaine', responsabilite: 'Simulation, distributions, corrélations et analyses', technologies: 'Python · NumPy · pandas · SciPy' },
      ],
      validation_checks: [
        { ordre: 1, controle: 'Tests Python', resultat: '359 / 359 réussis', lecture: 'Le socle métier et les workflows testés sont stables.' },
        { ordre: 2, controle: 'Build frontend', resultat: 'Réussi · 1 593 modules', lecture: 'TypeScript et Vite produisent une version de production.' },
        { ordre: 3, controle: 'Vérification Chromium', resultat: '4 vues contrôlées', lecture: 'Les écrans illustrés se chargent sans overlay d’erreur.' },
        { ordre: 4, controle: 'Reproductibilité', resultat: 'Graine 20260816', lecture: 'Le scénario de démonstration peut être rejoué à hypothèses constantes.' },
      ],
    },
  },
  sources,
};

writeFileSync(join(reportDir, 'artifact.json'), `${JSON.stringify(artifact, null, 2)}\n`, 'utf8');
console.log('artifact.json generated');
