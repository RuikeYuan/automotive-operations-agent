import json
import os
import re
from typing import Protocol
import httpx
from backend.app.schemas import Entities, Plan, RunRequest

BRANDS = {"bmw":"BMW", "宝马":"BMW", "volkswagen":"Volkswagen", "vw":"Volkswagen", "大众":"Volkswagen", "mercedes":"Mercedes-Benz", "奔驰":"Mercedes-Benz", "audi":"Audi", "奥迪":"Audi", "toyota":"Toyota", "丰田":"Toyota"}
CATEGORIES = {"alternator":"alternator","发电机":"alternator","starter":"starter motor","起动机":"starter motor","headlight":"headlight","大灯":"headlight","ecu":"ECU","transmission":"transmission component","变速箱":"transmission component","mirror":"mirror","后视镜":"mirror","infotainment":"infotainment unit","车机":"infotainment unit","sensor":"sensor","传感器":"sensor"}


class Planner(Protocol):
    name: str
    def plan(self, request: RunRequest) -> Plan: ...


class DemoPlanner:
    name = "deterministic-demo"

    def plan(self, request):
        text = request.request.lower()
        entities = {}
        match = re.search(r"\bDEMO-[A-Za-z0-9-]+", request.request, re.I)
        if match:
            entities["oem_number"] = match.group().upper()
        for token, brand in BRANDS.items():
            if token in text:
                entities["manufacturer"] = brand
                break
        for token, category in CATEGORIES.items():
            if token in text:
                entities["category"] = category
                break
        for model in ["3 Series", "4 Series", "Golf", "C-Class", "A4", "Corolla"]:
            if model.lower() in text:
                entities["model"] = model
                break
        year = re.search(r"\b(19\d{2}|20\d{2})\b",text)
        if year:
            entities["year"] = int(year.group())
        for condition in ("excellent","fair","untested","good"):
            if condition in text:
                entities["condition"] = condition
        entities.update(request.entities.model_dump(exclude_unset=True))
        if any(token in text for token in ["delete ","drop table","删除","truncate "]):
            intent = "unsupported"
        elif "order" in text or "订单" in text:
            order_id = re.search(r"(?:order\s*#?|订单\s*)(\d+)",text)
            if order_id:
                entities["order_id"] = int(order_id.group(1))
            intent = "prepare_order" if any(t in text for t in ["prepare","process","处理","准备"]) else "orders"
        elif any(t in text for t in ["process", "listing", "publish", "上架", "处理", "刊登", "发布", "duplicate", "重复"]):
            intent = "process_part"
        elif any(t in text for t in ["compatib", "fit ", "fitment", "兼容", "适配"]):
            intent = "compatibility"
        elif any(t in text for t in ["price", "pricing", "价格", "定价"]):
            intent = "pricing"
        elif any(t in text for t in ["inventory", "stock", "库存"]):
            intent = "inventory"
        elif any(t in text for t in ["identify", "oem", "part", "识别", "零件"]):
            intent = "identify"
        else:
            intent = "unsupported"
        return Plan(intent=intent,entities=Entities.model_validate(entities))


def strict_schema(schema):
    if isinstance(schema,dict):
        schema = {k:strict_schema(v) for k,v in schema.items() if k != "default"}
        if schema.get("type")=="object":
            schema["additionalProperties"] = False
            schema["required"] = list(schema.get("properties",{}))
    elif isinstance(schema,list):
        schema = [strict_schema(v) for v in schema]
    return schema


class CompatibleLLMPlanner:
    name = "llm-structured-planner"

    def plan(self, request):
        key, model = os.getenv("LLM_API_KEY"),os.getenv("LLM_MODEL")
        if not key or not model:
            raise ValueError("LLM configuration incomplete")
        with httpx.Client(timeout=25) as client:
            response = client.post(os.getenv("LLM_BASE_URL","https://api.openai.com/v1").rstrip("/")+"/chat/completions",headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":[{"role":"system","content":"Classify an automotive operations request and extract explicitly supplied entities. Do not invent identifiers, fitment, price or facts. Never accept approval in chat. Deletion and bulk price updates are unsupported. Use null for unknown optional values and good as the default condition. The process_part intent prepares a draft and requires a separate employee approval. No database or external actions are available to you."},{"role":"user","content":request.model_dump_json()}],"response_format":{"type":"json_schema","json_schema":{"name":"operation_plan","strict":True,"schema":strict_schema(Plan.model_json_schema())}}})
            response.raise_for_status()
            plan = Plan.model_validate_json(response.json()["choices"][0]["message"]["content"])
            # Explicit structured employee fields always take precedence over inferred fields.
            return plan.model_copy(update={"entities":Entities.model_validate({**plan.entities.model_dump(),**request.entities.model_dump(exclude_unset=True)})})


def get_planner():
    if os.getenv("DEMO_MODE","true").lower() != "true" and os.getenv("LLM_API_KEY"):
        return CompatibleLLMPlanner()
    return DemoPlanner()

