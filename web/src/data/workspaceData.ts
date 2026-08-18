export type RiskLevel = 'Critique' | 'Élevé' | 'Modéré' | 'Faible';
export type RiskStatus = 'Ouvert' | 'Sous traitement' | 'Sous surveillance' | 'Clôturé';

export type PortfolioRisk = {
  id: string;
  category: string;
  title: string;
  owner: string;
  probability: number;
  impact: number;
  exposure: number;
  level: RiskLevel;
  status: RiskStatus;
  treatment: string;
  nextReview: string;
};

export const portfolioRisks: PortfolioRisk[] = [
  { id: 'R-001', category: 'Technique', title: 'Sous-estimation de la charge de migration', owner: 'Nadia El Amrani', probability: 45, impact: 240_000, exposure: 108_000, level: 'Critique', status: 'Sous traitement', treatment: 'Pilote sur deux domaines prioritaires', nextReview: '21/08/2026' },
  { id: 'R-002', category: 'Réglementaire', title: 'Retard d’homologation de la plateforme', owner: 'Karim Benali', probability: 35, impact: 180_000, exposure: 63_000, level: 'Élevé', status: 'Sous traitement', treatment: 'Revue hebdomadaire avec la conformité', nextReview: '19/08/2026' },
  { id: 'R-003', category: 'Ressources', title: 'Indisponibilité d’un architecte clé', owner: 'Sophie Martin', probability: 25, impact: 220_000, exposure: 55_000, level: 'Élevé', status: 'Ouvert', treatment: 'Plan de succession à valider', nextReview: '20/08/2026' },
  { id: 'R-004', category: 'Sécurité', title: 'Vulnérabilité critique détectée avant mise en production', owner: 'Youssef Alaoui', probability: 15, impact: 350_000, exposure: 52_500, level: 'Élevé', status: 'Sous surveillance', treatment: 'Tests d’intrusion à chaque release', nextReview: '24/08/2026' },
  { id: 'R-005', category: 'Financier', title: 'Inflation des prestations externes', owner: 'Claire Moreau', probability: 40, impact: 90_000, exposure: 36_000, level: 'Modéré', status: 'Sous surveillance', treatment: 'Plafonnement contractuel des taux', nextReview: '31/08/2026' },
  { id: 'R-006', category: 'Fournisseur', title: 'Non-respect des SLA par l’intégrateur', owner: 'Nadia El Amrani', probability: 30, impact: 120_000, exposure: 36_000, level: 'Modéré', status: 'Sous traitement', treatment: 'Pénalités et comité de performance', nextReview: '26/08/2026' },
  { id: 'R-007', category: 'Données', title: 'Qualité insuffisante des données sources', owner: 'Omar Idrissi', probability: 35, impact: 80_000, exposure: 28_000, level: 'Modéré', status: 'Sous traitement', treatment: 'Règles de qualité automatisées', nextReview: '18/08/2026' },
  { id: 'R-008', category: 'Organisation', title: 'Adoption insuffisante par les équipes métier', owner: 'Leïla Mansouri', probability: 25, impact: 100_000, exposure: 25_000, level: 'Modéré', status: 'Ouvert', treatment: 'Réseau d’ambassadeurs et formation', nextReview: '28/08/2026' },
  { id: 'R-009', category: 'Opérationnel', title: 'Interruption de service pendant la bascule', owner: 'Youssef Alaoui', probability: 10, impact: 200_000, exposure: 20_000, level: 'Faible', status: 'Sous surveillance', treatment: 'Plan de retour arrière testé', nextReview: '02/09/2026' },
  { id: 'R-010', category: 'Gouvernance', title: 'Extension non maîtrisée du périmètre', owner: 'Pierre Dubois', probability: 30, impact: 150_000, exposure: 45_000, level: 'Élevé', status: 'Sous traitement', treatment: 'Comité de contrôle des changements', nextReview: '22/08/2026' },
];

export const simulationRuns = [
  { id: 'SIM-260816-03', scenario: 'Référence validée', author: 'Sophie Martin', iterations: '50 000', seed: '20260816', mean: '2,45 M€', p80: '4,12 M€', status: 'Validée', executedAt: '16/08/2026 · 18:42' },
  { id: 'SIM-260816-02', scenario: 'Plan de mitigation v2', author: 'Nadia El Amrani', iterations: '50 000', seed: '20260815', mean: '2,31 M€', p80: '3,55 M€', status: 'À approuver', executedAt: '16/08/2026 · 16:08' },
  { id: 'SIM-260815-06', scenario: 'Stress fournisseurs', author: 'Karim Benali', iterations: '100 000', seed: '20260814', mean: '2,86 M€', p80: '5,20 M€', status: 'Archivée', executedAt: '15/08/2026 · 11:26' },
  { id: 'SIM-260812-01', scenario: 'Référence – comité juillet', author: 'Sophie Martin', iterations: '50 000', seed: '20260731', mean: '2,39 M€', p80: '4,06 M€', status: 'Archivée', executedAt: '12/08/2026 · 09:14' },
];

export const teamMembers = [
  { initials: 'PD', name: 'Pierre Dubois', email: 'pierre.dubois@atlas-programme.ma', role: 'Administrateur', scope: 'Tous les projets', mfa: true, lastSeen: 'Aujourd’hui · 21:48', status: 'Actif' },
  { initials: 'SM', name: 'Sophie Martin', email: 'sophie.martin@atlas-programme.ma', role: 'Risk manager', scope: 'Projet Atlas', mfa: true, lastSeen: 'Aujourd’hui · 18:51', status: 'Actif' },
  { initials: 'NE', name: 'Nadia El Amrani', email: 'nadia.elamrani@atlas-programme.ma', role: 'Analyste', scope: 'Projet Atlas', mfa: true, lastSeen: 'Aujourd’hui · 17:32', status: 'Actif' },
  { initials: 'KB', name: 'Karim Benali', email: 'karim.benali@atlas-programme.ma', role: 'Contributeur', scope: 'Risques réglementaires', mfa: false, lastSeen: 'Hier · 15:10', status: 'Actif' },
  { initials: 'CM', name: 'Claire Moreau', email: 'claire.moreau@atlas-programme.ma', role: 'Lecteur', scope: 'Reporting exécutif', mfa: true, lastSeen: '14/08/2026 · 10:05', status: 'Suspendu' },
];

export const auditEvents = [
  { at: '16/08/2026 · 18:47', actor: 'Sophie Martin', action: 'Validation de la simulation SIM-260816-03', object: 'Scénario Référence' },
  { at: '16/08/2026 · 17:21', actor: 'Pierre Dubois', action: 'Modification du seuil d’approbation P80', object: 'Paramètres du projet' },
  { at: '16/08/2026 · 16:13', actor: 'Nadia El Amrani', action: 'Ajout de trois hypothèses documentées', object: 'Plan de mitigation v2' },
  { at: '15/08/2026 · 11:31', actor: 'Karim Benali', action: 'Export du rapport de sensibilité', object: 'Stress fournisseurs' },
];

export const documentationArticles = [
  { category: 'Prise en main', title: 'Préparer un registre de risques exploitable', description: 'Colonnes obligatoires, contrôles de qualité et conventions de saisie.', time: '6 min', updated: '12/08/2026', keywords: 'excel import registre qualité colonnes' },
  { category: 'Modélisation', title: 'Choisir une loi de distribution', description: 'Quand utiliser les lois triangulaire, PERT, normale ou log-normale.', time: '9 min', updated: '05/08/2026', keywords: 'distribution pert triangulaire normale' },
  { category: 'Modélisation', title: 'Documenter les hypothèses de calcul', description: 'Règles de traçabilité, sources et processus d’approbation.', time: '5 min', updated: '16/08/2026', keywords: 'hypothèses source validation gouvernance' },
  { category: 'Analyse', title: 'Interpréter P50, P80 et P90', description: 'Lecture des percentiles et traduction en réserve budgétaire.', time: '7 min', updated: '14/08/2026', keywords: 'percentile réserve budget p80 p90' },
  { category: 'Analyse', title: 'Lire une analyse de sensibilité', description: 'Comprendre Spearman et prioriser les plans de réponse.', time: '8 min', updated: '02/08/2026', keywords: 'spearman sensibilité contribution' },
  { category: 'Gouvernance', title: 'Valider et archiver une simulation', description: 'Workflow d’approbation, piste d’audit et règles de conservation.', time: '4 min', updated: '10/08/2026', keywords: 'validation archive audit conformité' },
];
