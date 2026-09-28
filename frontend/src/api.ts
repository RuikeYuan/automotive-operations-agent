export async function api<T>(path:string, body?:unknown):Promise<T> {
  const response = await fetch(`/api${path}`,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)})
  if (!response.ok) {
    const data = await response.json().catch(()=>({detail:`HTTP ${response.status}`}))
    throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail))
  }
  return response.json()
}
