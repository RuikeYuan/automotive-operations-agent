from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from backend.app.db import get_session
from backend.app.models import AgentRun, ToolExecution, ApprovalRequest, Listing, InventoryItem, MarketplaceRecord
from backend.app.schemas import RunRequest, ToolInput, InventoryLocationChange
from backend.app.agent.orchestrator import OperationsAgent
from backend.app.agent.providers import get_planner
from backend.app.agent.skills import SKILLS
from backend.app.tools import Tools
from backend.app.services.approvals import resolve_approval
from backend.app.services.inventory import propose_location_change
from integrations.marketplace import PolicyError

app = FastAPI(title="Automotive Operations AI Agent",version="0.1.0",description="Local synthetic automotive operations. All publishing is a mock.")


def row(model):
    return jsonable_encoder({c.name:getattr(model,c.name) for c in model.__table__.columns})


@app.exception_handler(SQLAlchemyError)
def database_error(request, error):
    return JSONResponse(status_code=503,content={"detail":"Database unavailable. No successful operation is claimed."})


@app.exception_handler(PolicyError)
def policy_error(request, error):
    return JSONResponse(status_code=409,content={"detail":str(error)})


@app.get("/health")
def health(session: Session=Depends(get_session)):
    session.execute(text("SELECT 1"))
    return {"status":"ok","database":"connected","provider":get_planner().name,"marketplace":"mock","synthetic":True}


@app.post("/agent/run",status_code=201)
def run_agent(body: RunRequest,session: Session=Depends(get_session)):
    return row(OperationsAgent(session).execute(body))


@app.get("/agent/runs")
def runs(session: Session=Depends(get_session),limit: int=Query(30,ge=1,le=100)):
    return [row(r) for r in session.scalars(select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit))]


@app.get("/agent/runs/{run_id}")
def get_run(run_id: str,session: Session=Depends(get_session)):
    result = session.get(AgentRun,run_id)
    if not result:
        raise HTTPException(404,"Run not found")
    return row(result)


@app.get("/agent/runs/{run_id}/trace")
def trace(run_id: str,session: Session=Depends(get_session)):
    get_run(run_id,session)
    return [row(r) for r in session.scalars(select(ToolExecution).where(ToolExecution.agent_run_id==run_id).order_by(ToolExecution.id))]


@app.get("/skills")
def skills():
    return [{"name":s.name,"purpose":s.purpose,"tools":s.tools,"specification":s.specification} for s in SKILLS.values()]


@app.get("/inventory")
def inventory(q: str=Query("",max_length=200),manufacturer: str|None=None,session: Session=Depends(get_session)):
    return Tools(session).call("search_inventory",{"query":q,"manufacturer":manufacturer})["data"]


@app.get("/inventory/{item_id}")
def inventory_item(item_id: int,session: Session=Depends(get_session)):
    try:
        return Tools(session).call("get_inventory_item",{"inventory_item_id":item_id})["data"]
    except LookupError as error:
        raise HTTPException(404,str(error))


@app.get("/parts/search")
def parts(q: str=Query("",max_length=200),session: Session=Depends(get_session)):
    return Tools(session).call("search_parts_catalog",{"query":q})


@app.patch("/inventory/{item_id}",status_code=202)
def propose_inventory_update(item_id: int,body: InventoryLocationChange,session: Session=Depends(get_session)):
    try:
        return row(propose_location_change(session,item_id,body.warehouse_location))
    except LookupError as error:
        raise HTTPException(404,str(error))


@app.get("/orders")
def orders(status: str|None=None,manufacturer: str|None=None,today: bool=False,session: Session=Depends(get_session)):
    return Tools(session).call("get_orders",{"status":status,"manufacturer":manufacturer,"today":today})["data"]


@app.get("/approvals")
def approvals(status: str|None=None,session: Session=Depends(get_session)):
    statement = select(ApprovalRequest)
    if status:
        statement = statement.where(ApprovalRequest.status==status)
    return [row(r) for r in session.scalars(statement.order_by(ApprovalRequest.id.desc()).limit(200))]


def resolve(request,approval_id,approve,session):
    if not request.headers.get("content-type","").startswith("application/json"):
        raise HTTPException(415,"Use application/json for review actions")
    try:
        return row(resolve_approval(session,approval_id,approve))
    except LookupError as error:
        raise HTTPException(404,str(error))
    except ConnectionError:
        raise HTTPException(503,"Mock marketplace unavailable. Nothing published; approval remains pending for retry.")


@app.post("/approvals/{approval_id}/approve")
def approve(approval_id: int,request: Request,session: Session=Depends(get_session)):
    return resolve(request,approval_id,True,session)


@app.post("/approvals/{approval_id}/reject")
def reject(approval_id: int,request: Request,session: Session=Depends(get_session)):
    return resolve(request,approval_id,False,session)


@app.get("/listings")
def listings(session: Session=Depends(get_session)):
    return [row(r) for r in session.scalars(select(Listing).order_by(Listing.id.desc()).limit(200))]


@app.get("/marketplace")
def marketplace(session: Session=Depends(get_session)):
    return [row(r) for r in session.scalars(select(MarketplaceRecord).order_by(MarketplaceRecord.id.desc()).limit(200))]


@app.get("/metrics")
def metrics(session: Session=Depends(get_session)):
    runs = session.scalars(select(AgentRun)).all()
    tools = session.scalars(select(ToolExecution)).all()
    approvals = session.scalars(select(ApprovalRequest)).all()
    done = [r for r in runs if r.completed_at]
    duration = [(r.completed_at-r.started_at).total_seconds() for r in done]
    return {"synthetic":True,"runs":len(runs),"inventory_records":session.scalar(select(func.count()).select_from(InventoryItem)),"pending_approvals":sum(a.status=="pending" for a in approvals),"published_mock":session.scalar(select(func.count()).select_from(MarketplaceRecord)),"tool_calls":len(tools),"tool_failure_rate":sum(t.execution_status=="error" for t in tools)/len(tools) if tools else None,"approval_rate":sum(a.status=="approved" for a in approvals)/sum(a.status in ("approved","rejected") for a in approvals) if any(a.status in ("approved","rejected") for a in approvals) else None,"completed_rate":sum(r.status=="completed" for r in runs)/len(runs) if runs else None,"average_completed_run_seconds":sum(duration)/len(duration) if duration else None}

