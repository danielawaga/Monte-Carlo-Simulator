import { useState } from 'react';
import { Plus, Save, Trash2 } from 'lucide-react';
import { Button, Card, CardTitle, StatusPill } from '../common';

type Assumption = {
  id: number;
  name: string;
  value: string;
  source: string;
};

const INITIAL_ASSUMPTIONS: Assumption[] = [
  { id: 1, name: "Taux d’inflation annuel", value: '2,5 %', source: 'Prévision économique du projet' },
  { id: 2, name: 'Corrélation entre les risques', value: 'Indépendants', source: 'Hypothèse conservatrice' },
  { id: 3, name: "Horizon d’analyse", value: '31/12/2026', source: 'Date de fin approuvée par le comité de pilotage' },
];

export function AssumptionsSection() {
  const [assumptions, setAssumptions] = useState(INITIAL_ASSUMPTIONS);
  const [saved, setSaved] = useState(false);

  const updateAssumption = (id: number, field: keyof Omit<Assumption, 'id'>, value: string) => {
    setAssumptions((current) => current.map((assumption) => assumption.id === id ? { ...assumption, [field]: value } : assumption));
    setSaved(false);
  };

  const addAssumption = () => {
    setAssumptions((current) => [
      ...current,
      { id: Math.max(0, ...current.map(({ id }) => id)) + 1, name: '', value: '', source: '' },
    ]);
    setSaved(false);
  };

  const removeAssumption = (id: number) => {
    setAssumptions((current) => current.filter((assumption) => assumption.id !== id));
    setSaved(false);
  };

  return (
    <Card className="assumptions-card">
      <CardTitle
        info={false}
        action={<Button type="button" onClick={addAssumption}><Plus />Ajouter une hypothèse</Button>}
      >
        Hypothèses de la simulation
      </CardTitle>
      <p className="assumptions-intro">Documentez les hypothèses utilisées afin de garantir la traçabilité et la bonne interprétation des résultats.</p>
      <div className="assumptions-head" aria-hidden="true"><span>Hypothèse</span><span>Valeur retenue</span><span>Justification ou source</span><span /></div>
      <div className="assumptions-list">
        {assumptions.map((assumption, index) => (
          <div className="assumption-row" key={assumption.id}>
            <label>
              <span className="sr-only">Nom de l’hypothèse {index + 1}</span>
              <input value={assumption.name} placeholder="Ex. Taux de change" onChange={(event) => updateAssumption(assumption.id, 'name', event.target.value)} />
            </label>
            <label>
              <span className="sr-only">Valeur de l’hypothèse {index + 1}</span>
              <input value={assumption.value} placeholder="Ex. 1,08" onChange={(event) => updateAssumption(assumption.id, 'value', event.target.value)} />
            </label>
            <label>
              <span className="sr-only">Justification de l’hypothèse {index + 1}</span>
              <input value={assumption.source} placeholder="Source ou commentaire" onChange={(event) => updateAssumption(assumption.id, 'source', event.target.value)} />
            </label>
            <Button type="button" aria-label={`Supprimer l’hypothèse ${index + 1}`} onClick={() => removeAssumption(assumption.id)}><Trash2 /></Button>
          </div>
        ))}
      </div>
      <div className="assumptions-footer">
        <span>{assumptions.length} hypothèse{assumptions.length > 1 ? 's' : ''} renseignée{assumptions.length > 1 ? 's' : ''}</span>
        <div>{saved ? <StatusPill>Hypothèses enregistrées</StatusPill> : null}<Button type="button" variant="primary" onClick={() => setSaved(true)}><Save />Enregistrer les hypothèses</Button></div>
      </div>
    </Card>
  );
}
