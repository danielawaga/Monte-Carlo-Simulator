export type RiskItem={id:string;category:string;risk:string;impact:string;probability:string;distribution:string;status:string;coefficient?:string;level?:'Élevé'|'Modéré'|'Faible'};
export type SimulationConfig={simulations:number;seed:number;levels:number[]};
export type SimulationSummary={mean:string;p80:string;p90:string;exceedance:string;baseline:string;reserve:string};
export type Scenario={name:string;color:'blue'|'green';description:string;p80:string;p90:string;reserve:string};
