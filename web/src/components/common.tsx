import type{ButtonHTMLAttributes,ReactNode}from'react';import{ChevronDown,Info}from'lucide-react';
export function Button({variant='secondary',children,...p}:ButtonHTMLAttributes<HTMLButtonElement>&{variant?:'primary'|'secondary'}){return <button className={'button '+variant} {...p}>{children}</button>}
export function PageHeader({title,subtitle,actions}: {title:string;subtitle:string;actions?:ReactNode}){return <header className="page-header"><div><h1>{title}</h1><p>{subtitle}</p></div><div className="header-actions">{actions}</div></header>}
export function Card({children,className=''}:{children:ReactNode;className?:string}){return <section className={'card '+className}>{children}</section>}
export function CardTitle({children,info=true,action}:{children:ReactNode;info?:boolean;action?:ReactNode}){return <div className="card-title"><h2>{children}{info&&<Info/>}</h2>{action}</div>}
export function StatusPill({children,tone='green'}:{children:ReactNode;tone?:'green'|'orange'|'blue'|'red'|'gray'}){return <span className={'pill '+tone}>{children}</span>}
export function SelectButton({children,...props}:ButtonHTMLAttributes<HTMLButtonElement>&{children:ReactNode}){return <Button {...props}>{children}<ChevronDown/></Button>}
