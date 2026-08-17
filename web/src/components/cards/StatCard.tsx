import{CircleDollarSign,Coins,ShieldCheck,TriangleAlert}from'lucide-react';import type{ReactNode}from'react';
const icons={money:CircleDollarSign,coins:Coins,shield:ShieldCheck,alert:TriangleAlert};
export function StatCard({label,value,sub,icon='coins'}:{label:string;value:string;sub?:string;icon?:keyof typeof icons}){const Icon=icons[icon];return <div className="stat card"><span className="stat-icon"><Icon/></span><div><label>{label}</label><strong>{value}</strong>{sub&&<small>{sub}</small>}</div></div>}
export function Metric({label,value,sub}:{label:string;value:string;sub:string}){return <div className="metric"><label>{label}</label><strong>{value}</strong><small>{sub}</small></div>}
