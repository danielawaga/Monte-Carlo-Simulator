export type RiskItem={id:string;category:string;risk:string;impact:string;probability:string;distribution:string;status:string;coefficient?:string;level?:'Critique'|'Élevé'|'Modéré'|'Faible'};
export type SimulationConfig={simulations:number;seed:number;levels:number[]};
export type AnalysisType='cost'|'duration';
export type ProjectSource='new'|'imported'|null;
export type DistributionName='triangular'|'pert'|'uniform'|'normal'|'lognormal'|'event';
export type RiskDraft={
  id:string;
  name:string;
  distribution:DistributionName;
  minimum:number|null;
  mostLikely:number|null;
  maximum:number|null;
  mean:number|null;
  standardDeviation:number|null;
  probability:number|null;
  impact:number|null;
  lambdaShape:number|null;
  category:string;
  unit:string;
  enabled:boolean;
  notes:string;
};
export type RiskRegisterDraft={
  schemaVersion:'1.0';
  metadata:{projectName:string;analysisType:AnalysisType;defaultUnit:string;baselineEstimate:number|null;description:string};
  items:RiskDraft[];
  correlations:{mode:'independent'|'correlated';names:string[];values:number[][]};
};
export type SimulationWorkspaceConfig=SimulationConfig&{
  decisionPercentile:number;
  exceedanceThreshold:number|null;
  convergenceTolerance:number;
  samplingMethod:'pseudo-random';
  scenarioName:string;
  scenarioDescription:string;
};
export type SavedScenario={
  id:string;
  name:string;
  description:string;
  savedAt:string;
  config:SimulationWorkspaceConfig;
  register:RiskRegisterDraft;
};
export type RegisterValidation={valid:boolean;projectName:string;totalItems:number;activeItems:number;correlationsEnabled:boolean};
export type NumericRecord=Record<string,number|string|boolean|null>;
export type SimulationResponse={
  project:{name:string;analysisType:string;unit:string;baseline:number|null};
  run:{simulations:number;seed:number;confidenceLevels:number[];correlationsEnabled:boolean;generatedAt:string};
  summary:NumericRecord;
  percentiles:NumericRecord[];
  sensitivity:NumericRecord[];
  convergence:NumericRecord[];
  baselineComparison:NumericRecord[];
  correlationDiagnostics:NumericRecord[];
  histogram:{start:number;end:number;count:number}[];
  sCurve:{amount:number;probability:number}[];
};

export type SavedRegister = {
  id: number;
  name: string;
  register: RiskRegisterDraft;
  createdAt: string;
  updatedAt: string;
};

export type SavedRun = {
  id: number;
  registerId: number | null;
  label: string;
  config: SimulationWorkspaceConfig;
  result: SimulationResponse;
  createdAt: string;
};

export type StorageInfo = {
  databasePath: string;
  registers: number;
  runs: number;
};
