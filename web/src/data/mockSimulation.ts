import type {RiskItem,Scenario,SimulationSummary} from '../types';
export const risks:RiskItem[]=[
 {id:'R-001',category:'Technique',risk:'Sous-estimation de la charge de migration',impact:'240 000 €',probability:'45 %',distribution:'PERT',status:'Sous traitement',coefficient:'+0,62',level:'Critique'},
 {id:'R-002',category:'Réglementaire',risk:"Retard d’homologation de la plateforme",impact:'180 000 €',probability:'35 %',distribution:'Triangulaire',status:'Sous traitement',coefficient:'+0,48',level:'Élevé'},
 {id:'R-003',category:'Ressources',risk:"Indisponibilité d’un architecte clé",impact:'220 000 €',probability:'25 %',distribution:'Triangulaire',status:'Ouvert',coefficient:'−0,22',level:'Élevé'},
 {id:'R-004',category:'Sécurité',risk:'Vulnérabilité critique détectée avant mise en production',impact:'350 000 €',probability:'15 %',distribution:'Lognormale',status:'Sous surveillance',coefficient:'+0,31',level:'Élevé'},
 {id:'R-005',category:'Financier',risk:'Inflation des prestations externes',impact:'90 000 €',probability:'40 %',distribution:'PERT',status:'Sous surveillance',coefficient:'+0,18',level:'Modéré'}];
export const summary:SimulationSummary={mean:'2 450 000 €',p80:'4 120 000 €',p90:'6 240 000 €',exceedance:'20 %',baseline:'2 100 000 €',reserve:'2 020 000 €'};
export const scenarios:Scenario[]=[{name:'Référence',color:'blue',description:'Dernière version validée · SIM-260816-03',p80:'4,12 M€',p90:'6,24 M€',reserve:'2,02 M€'},{name:'Mitigation',color:'green',description:'Plan de réponse v2 · À approuver',p80:'3,55 M€',p90:'5,10 M€',reserve:'1,45 M€'}];
export const comparison=[['Valeur minimale','1,85 M€','1,72 M€','−0,13 M€','−7 %'],['Valeur moyenne','2,45 M€','2,31 M€','−0,14 M€','−6 %'],['P80','4,12 M€','3,55 M€','−0,57 M€','−14 %'],['P90','6,24 M€','5,10 M€','−1,14 M€','−18 %'],['Probabilité de dépassement > 5 M€','20 %','12 %','−8 pts','−40 %'],['Réserve recommandée (P80)','2,02 M€','1,45 M€','−0,57 M€','−28 %']];
