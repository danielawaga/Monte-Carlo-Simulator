import type {RiskItem,Scenario,SimulationSummary} from '../types';
export const risks:RiskItem[]=[
 {id:'R-01',category:'Technique',risk:"Retard de livraison d’un composant critique",impact:'120 000 €',probability:'30 %',distribution:'Triangulaire',status:'Actif',coefficient:'+0,48',level:'Élevé'},
 {id:'R-02',category:'Ressources',risk:"Indisponibilité d’une ressource clé",impact:'80 000 €',probability:'25 %',distribution:'Triangulaire',status:'Actif',coefficient:'−0,22',level:'Modéré'},
 {id:'R-03',category:'Externe',risk:'Évolution réglementaire défavorable',impact:'150 000 €',probability:'20 %',distribution:'Pert',status:'Actif',coefficient:'+0,18',level:'Faible'},
 {id:'R-04',category:'Technique',risk:"Sous-estimation de l’effort de développement",impact:'200 000 €',probability:'40 %',distribution:'Pert',status:'Actif',coefficient:'+0,62',level:'Élevé'},
 {id:'R-05',category:'Financier',risk:'Inflation des coûts des matériaux',impact:'60 000 €',probability:'35 %',distribution:'Triangulaire',status:'Actif',coefficient:'+0,31',level:'Modéré'}];
export const summary:SimulationSummary={mean:'2 450 000 €',p80:'4 120 000 €',p90:'6 240 000 €',exceedance:'20 %',baseline:'2 100 000 €',reserve:'2 020 000 €'};
export const scenarios:Scenario[]=[{name:'Référence',color:'blue',description:'Scénario de référence actuel',p80:'80,0 M €',p90:'120,0 M €',reserve:'80,0 M €'},{name:'Mitigation',color:'green',description:'Scénario avec plans de mitigation',p80:'65,0 M €',p90:'95,0 M €',reserve:'65,0 M €'}];
export const comparison=[['Valeur minimale','12,0 M €','9,0 M €','−3,0 M €','−25 %'],['Valeur moyenne','58,3 M €','44,2 M €','−14,1 M €','−24 %'],['P80','80,0 M €','65,0 M €','−15,0 M €','−19 %'],['P90','120,0 M €','95,0 M €','−25,0 M €','−21 %'],['Probabilité de dépassement > 100 M €','35 %','22 %','−13 pts','−37 %'],['Réserve recommandée (P80)','80,0 M €','65,0 M €','−15,0 M €','−19 %']];
