from uuid import uuid4
from time import perf_counter
from pydantic import ValidationError
from backend.app.models import AgentRun, ToolExecution, ApprovalRequest, Listing, now
from backend.app.tools import Tools
from backend.app.agent.providers import get_planner, DemoPlanner
from backend.app.agent.skills import SKILLS, INTENT_SKILLS
from backend.app.observability import sanitize
from backend.app.services.approvals import request_publish


class OperationsAgent:
    def __init__(self, session, planner=None, knowledge=None):
        self.session, self.planner = session, planner or get_planner()
        self.tools = Tools(session,knowledge)
        self.traces = []

    def call(self, skill, tool, **arguments):
        if tool not in SKILLS[skill].tools:
            raise ValueError("Tool is not allowed by selected skill")
        started = perf_counter()
        trace = dict(agent_run_id=self.run.id, selected_skill=skill, tool_name=tool, input=sanitize(arguments), output={}, execution_status="success", error=None, summary=SKILLS[skill].purpose)
        try:
            result = self.tools.call(tool,arguments)
            trace["output"] = sanitize(result)
            self.state["tool_results"][tool] = result
            self.state["completed_steps"].append(tool)
            return result["data"]
        except Exception as error:
            trace.update(execution_status="error",error=type(error).__name__)
            raise
        finally:
            trace["duration"] = (perf_counter()-started)*1000
            self.traces.append(trace)

    def execute(self, request):
        self.run = AgentRun(id=str(uuid4()),user_request=sanitize(request.request),status="running",state={},final_response={})
        self.session.add(self.run)
        self.session.commit()
        self.state = {"request":sanitize(request.request),"intent":None,"known_entities":{},"missing_information":[],"plan":[],"skills":[],"completed_steps":[],"pending_steps":[],"tool_results":{},"approval_required":False,"status":"running","provider":self.planner.name,"warnings":[]}
        try:
            try:
                plan = self.planner.plan(request)
            except ValidationError:
                return self.finish("needs_information",{"message":"OEM or extracted fields are malformed. Provide a valid catalog OEM and vehicle details.","missing_information":["valid_oem_number"]})
            except Exception as error:
                self.state["warnings"].append(f"AI planner unavailable ({type(error).__name__}); deterministic fallback used.")
                self.state["provider"] = "deterministic-fallback"
                plan = DemoPlanner().plan(request)
            e = plan.entities
            skills = INTENT_SKILLS[plan.intent]
            self.state.update(intent=plan.intent,known_entities=e.model_dump(exclude_none=True),skills=skills,plan=[{"skill":s,"purpose":SKILLS[s].purpose,"tools":list(SKILLS[s].tools),"specification":f"skills/{s}/SKILL.md"} for s in skills])
            # Ensure deployed skill specifications exist; runtime uses the audited allowlists above.
            for s in skills:
                SKILLS[s].specification
            if plan.intent == "unsupported":
                return self.finish("needs_information",{"message":"Supported tasks: identify parts, check stock/fitment/pricing, prepare listings, and review orders. Destructive operations are unavailable."})
            if plan.intent in ("orders","prepare_order"):
                text = request.request.lower()
                orders = self.call("order-processing","get_orders",order_id=e.order_id,manufacturer=e.manufacturer,today=any(t in text for t in ["today","今天"]),status="awaiting_shipment" if any(t in text for t in ["waiting","待发货"]) else None)
                if plan.intent == "orders":
                    return self.finish("completed",orders)
                if not e.order_id or len(orders["orders"])!=1:
                    return self.finish("needs_information",{"message":"Provide an existing order ID.","missing_information":["order_id"]})
                order = orders["orders"][0]
                if order["status"] != "awaiting_shipment":
                    return self.finish("needs_information",{"message":"Only orders awaiting shipment can be prepared."})
                approval = ApprovalRequest(agent_run_id=self.run.id,action_type="prepare_order",payload={"order_id":e.order_id,"previous_status":order["status"],"new_status":"processing"},status="pending")
                self.session.add(approval)
                self.session.flush()
                return self.finish("awaiting_approval",{**orders,"approval_id":approval.id,"message":"Review the proposed order status change."})
            if plan.intent == "inventory":
                return self.finish("completed",self.call("inventory-management","search_inventory",oem_number=e.oem_number,manufacturer=e.manufacturer,category=e.category))
            identification = self.call("part-identification","lookup_oem",oem_number=e.oem_number) if e.oem_number else self.call("part-identification","search_parts_catalog",query=request.request,manufacturer=e.manufacturer,category=e.category,model=e.model,year=e.year,vin=e.vin)
            candidates = identification["candidate_parts"]
            if len(candidates)!=1:
                return self.finish("needs_information",{"identification":identification,"message":"Confirm the OEM number from the physical part; identification is ambiguous or unknown.","missing_information":identification["missing_information"]})
            part = candidates[0]
            if e.manufacturer and part["manufacturer"].lower()!=e.manufacturer.lower() and plan.intent!="compatibility":
                return self.finish("needs_information",{"message":"Manufacturer and OEM disagree. Confirm the physical part.","missing_information":["confirmed_manufacturer"],"identification":identification})
            result = {"part":part,"identification":identification,"synthetic":True}
            if plan.intent == "identify":
                return self.finish("completed",result)
            if plan.intent in ("process_part","compatibility"):
                target = dict(manufacturer=e.target_manufacturer,model=e.target_model,year=e.target_year)
                if plan.intent=="compatibility" and not any(target.values()):
                    target = dict(manufacturer=e.manufacturer,model=e.model,year=e.year)
                result["compatibility"] = self.call("compatibility-check","check_vehicle_compatibility",part_id=part["id"],**target)
                if plan.intent=="compatibility":
                    return self.finish("completed",result)
            if plan.intent=="process_part":
                result["inventory"] = self.call("inventory-management","search_inventory",part_id=part["id"])
                result["duplicates"] = self.call("duplicate-detection","find_duplicates",part_id=part["id"])
            result["history"] = self.call("pricing","get_historical_sales",part_id=part["id"])
            result["pricing"] = self.call("pricing","calculate_suggested_price",part_id=part["id"],condition=e.condition)
            if plan.intent=="pricing":
                return self.finish("completed",result)
            result["inventory_draft"] = self.call("inventory-management","create_inventory_draft",part_id=part["id"],price=result["pricing"]["suggested_price"],condition=e.condition)
            result["listing"] = self.call("listing-generation","generate_listing_draft",inventory_item_id=result["inventory_draft"]["id"],condition=e.condition)
            approval = request_publish(self.session,self.run.id,self.session.get(Listing,result["listing"]["listing_id"]))
            result.update(approval_id=approval.id,message="Listing drafted from verified demo facts. Review duplicate candidates and approve separately before mock publication.")
            return self.finish("awaiting_approval",result)
        except Exception as error:
            run_id = self.run.id
            self.session.rollback()
            self.run = self.session.get(AgentRun,run_id)
            self.state["rolled_back"] = True
            return self.finish("failed",{"message":"Operation failed safely. Unfinished changes were rolled back.","error":type(error).__name__})

    def finish(self,status,result):
        self.state.update(status=status,approval_required=status=="awaiting_approval",pending_steps=["human_approval"] if status=="awaiting_approval" else [],missing_information=result.get("missing_information",[]))
        self.run.status = status
        self.run.state = sanitize(self.state)
        self.run.final_response = sanitize(result)
        self.run.completed_at = None if status=="awaiting_approval" else now()
        for trace in self.traces:
            self.session.add(ToolExecution(**trace))
        self.session.commit()
        return self.run

