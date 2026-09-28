export type Json = Record<string, any>
export interface Run {id:string; user_request:string; status:string; started_at:string; final_response:Json; state:{intent:string; provider:string; skills:string[]; plan:{skill:string;purpose:string;tools:string[]}[]; warnings:string[]; missing_information:string[]}}
export interface Trace {id:number; selected_skill:string; tool_name:string; input:Json; output:Json; execution_status:string; duration:number; summary:string; error:string|null}
export interface Approval {id:number; agent_run_id:string; action_type:string; payload:Json; status:string; created_at:string; resolution:Json}
export interface Inventory {id:number;name:string;oem_number:string;manufacturer:string;category:string;internal_sku:string;quantity:number;warehouse_location:string;status:string;asking_price:number}
