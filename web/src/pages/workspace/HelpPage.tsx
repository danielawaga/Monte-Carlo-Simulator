import { useState } from 'react';
import { ArrowRight, BookOpen, CheckCircle2, Clock3, FileSpreadsheet, Mail, Search, ShieldCheck, X } from 'lucide-react';
import { Card, CardTitle, PageHeader, StatusPill } from '../../components/common';
import { documentationArticles } from '../../data/workspaceData';

const glossary = [
  ['P80', 'Valeur qui n’est dépassée que dans 20 % des simulations.'],
  ['Réserve', 'Écart entre le percentile d’engagement et le budget de référence.'],
  ['Spearman', 'Coefficient mesurant l’influence d’un risque sur le résultat total.'],
  ['Graine', 'Valeur permettant de reproduire exactement une simulation.'],
];

const articleGuidance: Record<string, string[]> = {
  'Préparer un registre de risques exploitable': ['Nommer un propriétaire et une date de revue pour chaque risque.', 'Exprimer la probabilité et les impacts dans des unités homogènes.', 'Contrôler les doublons, valeurs manquantes et distributions avant import.'],
  'Choisir une loi de distribution': ['Utiliser une loi triangulaire lorsque trois estimations expertes sont disponibles.', 'Privilégier PERT pour réduire le poids des valeurs extrêmes.', 'Réserver la loi log-normale aux coûts strictement positifs et asymétriques.'],
  'Documenter les hypothèses de calcul': ['Associer une source vérifiable et une date d’arrêté à chaque hypothèse.', 'Identifier le responsable métier qui valide la valeur.', 'Créer une nouvelle version dès qu’une hypothèse approuvée évolue.'],
  'Interpréter P50, P80 et P90': ['P50 représente la médiane, pas une garantie de maîtrise budgétaire.', 'P80 constitue le niveau d’engagement retenu par la gouvernance Atlas.', 'P90 sert à éclairer l’exposition résiduelle et les scénarios de stress.'],
  'Lire une analyse de sensibilité': ['Classer les risques par valeur absolue du coefficient de Spearman.', 'Vérifier le sens du coefficient avant de définir une réponse.', 'Rejouer la simulation après modification d’un risque prioritaire.'],
  'Valider et archiver une simulation': ['Figer le registre, les hypothèses, la graine et la version du moteur.', 'Faire approuver le résultat par un utilisateur habilité.', 'Conserver l’export, la synthèse et le journal d’audit pendant sept ans.'],
};

export function HelpPage() {
  const [query, setQuery] = useState('');
  const [selectedArticle, setSelectedArticle] = useState<string | null>(null);
  const normalizedQuery = query.toLocaleLowerCase('fr');
  const filteredArticles = documentationArticles.filter((article) => `${article.title} ${article.description} ${article.category} ${article.keywords}`.toLocaleLowerCase('fr').includes(normalizedQuery));

  return (
    <>
      <PageHeader title="Centre d’aide et méthodologie" subtitle="Documentation fonctionnelle, référentiel de modélisation et assistance." />

      <Card className="help-search-card">
        <div><BookOpen /><span><b>Comment pouvons-nous vous aider ?</b><small>Recherchez un concept, une procédure ou une fonctionnalité.</small></span></div>
        <label className="search-field"><Search /><span className="sr-only">Rechercher dans la documentation</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ex. P80, import Excel, hypothèses…" /></label>
      </Card>

      <div className="help-overview-grid">
        <Card className="onboarding-card">
          <CardTitle info={false}>Parcours de prise en main</CardTitle>
          <ol>
            <li className="done"><CheckCircle2 /><div><b>Structurer le registre de risques</b><span>Modèle conforme importé le 16/08/2026</span></div></li>
            <li className="done"><CheckCircle2 /><div><b>Documenter les hypothèses</b><span>3 hypothèses enregistrées</span></div></li>
            <li className="current"><Clock3 /><div><b>Faire approuver le scénario de mitigation</b><span>Validation du risk manager attendue</span></div></li>
            <li><ShieldCheck /><div><b>Présenter la réserve au comité</b><span>Rapport exécutif à préparer</span></div></li>
          </ol>
        </Card>
        <Card className="support-card">
          <Mail /><div><StatusPill>Support entreprise</StatusPill><h2>Besoin d’un accompagnement ?</h2><p>Assistance fonctionnelle du lundi au vendredi, 08:30–18:00. Délai de première réponse inférieur à 4 heures ouvrées.</p><a className="button secondary" href="mailto:support@risksim.fr?subject=Assistance%20Projet%20Atlas"><Mail />Contacter le support</a></div>
        </Card>
      </div>

      <section className="docs-section">
        <div className="section-heading"><div><h2>Guides et procédures</h2><p>{filteredArticles.length} ressource{filteredArticles.length > 1 ? 's' : ''} correspondant à votre recherche.</p></div></div>
        <div className="docs-grid">
          {filteredArticles.map((article) => <article className="doc-card card" key={article.title}><div><span>{article.category}</span><FileSpreadsheet /></div><h3>{article.title}</h3><p>{article.description}</p><footer><small><Clock3 />{article.time} · Mis à jour le {article.updated}</small><button type="button" aria-label={`Ouvrir ${article.title}`} onClick={() => setSelectedArticle(article.title)}><ArrowRight /></button></footer></article>)}
        </div>
        {filteredArticles.length === 0 ? <div className="pro-empty-state"><Search /><b>Aucune ressource trouvée</b><span>Essayez un terme plus général ou contactez le support.</span></div> : null}
        {selectedArticle ? <Card className="article-reader">
          <div><div><span>Fiche méthode</span><h3>{selectedArticle}</h3></div><button type="button" aria-label="Fermer l’article" onClick={() => setSelectedArticle(null)}><X /></button></div>
          <p>{documentationArticles.find((article) => article.title === selectedArticle)?.description}</p>
          <ol>{articleGuidance[selectedArticle].map((guidance) => <li key={guidance}><CheckCircle2 /><span>{guidance}</span></li>)}</ol>
          <small>Référentiel RiskSim · Projet Atlas · Version applicable au 17/08/2026</small>
        </Card> : null}
      </section>

      <div className="pro-help-bottom">
        <Card className="pro-panel">
          <CardTitle info={false}>Glossaire de référence</CardTitle>
          <dl className="glossary-list">{glossary.map(([term, definition]) => <div key={term}><dt>{term}</dt><dd>{definition}</dd></div>)}</dl>
        </Card>
        <Card className="pro-panel faq-card">
          <CardTitle info={false}>Questions fréquentes</CardTitle>
          <details><summary>Combien d’itérations faut-il exécuter ?</summary><p>50 000 itérations conviennent au reporting courant. Utilisez 100 000 pour les analyses de convergence ou les queues de distribution.</p></details>
          <details><summary>Une simulation validée peut-elle être modifiée ?</summary><p>Non. Toute modification crée une nouvelle version afin de préserver la piste d’audit.</p></details>
          <details><summary>Comment traiter les risques corrélés ?</summary><p>Documentez la relation dans les hypothèses puis renseignez une matrice de corrélation approuvée.</p></details>
        </Card>
      </div>
    </>
  );
}
