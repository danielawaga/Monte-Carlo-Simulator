import { ExternalLink, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { risks } from '../../data/mockSimulation';
import { Card, CardTitle, StatusPill } from '../common';

export function RiskPreviewTable() {
  return (
    <Card>
      <CardTitle
        info={false}
        action={<div className="table-actions"><Link className="button secondary" to="/risques">Voir tous les risques <ExternalLink /></Link><span>10 risques</span><span><RefreshCw />Synchronisé à 17:54</span></div>}
      >
        Aperçu des risques importés
      </CardTitle>
      <div className="table-wrap">
        <table>
          <thead><tr>{['ID', 'Catégorie', 'Risque', 'Impact (P50)', 'Probabilité', 'Distribution', 'Statut'].map((heading) => <th key={heading}>{heading}</th>)}</tr></thead>
          <tbody>{risks.map((risk) => <tr key={risk.id}><td>{risk.id}</td><td>{risk.category}</td><td className="dark">{risk.risk}</td><td>{risk.impact}</td><td>{risk.probability}</td><td>{risk.distribution}</td><td><StatusPill>{risk.status}</StatusPill></td></tr>)}</tbody>
        </table>
      </div>
      <div className="pagination"><span>Affichage des 5 risques les plus contributifs sur 10.</span><span>Registre v2026.08.16</span></div>
    </Card>
  );
}
