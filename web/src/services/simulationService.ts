import {comparison,risks,scenarios,summary} from '../data/mockSimulation';
// Contrat d'adaptation prêt à être remplacé par des appels HTTP au moteur Python.
export const simulationService={async getRisks(){return risks},async getSummary(){return summary},async getScenarios(){return scenarios},async getComparison(){return comparison}};
