import json
import pytest
import httpx
from backend.app.agent.providers import CompatibleLLMPlanner, DemoPlanner, get_planner
from backend.app.agent.orchestrator import OperationsAgent
from backend.app.schemas import RunRequest


def test_demo_mode_wins_over_key(monkeypatch):
    monkeypatch.setenv("DEMO_MODE","true")
    monkeypatch.setenv("LLM_API_KEY","test-fixture-key")
    assert isinstance(get_planner(),DemoPlanner)


def test_llm_path_validates_and_executes_tools(session,monkeypatch):
    monkeypatch.setenv("DEMO_MODE","false")
    monkeypatch.setenv("LLM_API_KEY","test-fixture-key")
    monkeypatch.setenv("LLM_MODEL","test-fixture-model")
    def response(client,url,**kwargs):
        assert url.endswith("/chat/completions")
        assert kwargs["json"]["response_format"]["json_schema"]["strict"]
        return httpx.Response(200,json={"choices":[{"message":{"content":json.dumps({"intent":"identify","entities":{"oem_number":"DEMO-BMW-ALT-001"}})}}]},request=httpx.Request("POST",url))
    monkeypatch.setattr(httpx.Client,"post",response)
    run = OperationsAgent(session).execute(RunRequest(request="Identify the part OEM DEMO-BMW-ALT-001"))
    assert run.status=="completed"
    assert run.state["provider"]=="llm-structured-planner"
    assert list(run.state["tool_results"])==["lookup_oem"]


def test_llm_failure_has_visible_fallback(session):
    class OfflinePlanner:
        name="test-offline-planner"
        def plan(self,request):
            raise ConnectionError("fixture outage")
    run = OperationsAgent(session,OfflinePlanner()).execute(RunRequest(request="Identify DEMO-BMW-ALT-001"))
    assert run.status=="completed"
    assert run.state["provider"]=="deterministic-fallback"
    assert run.state["warnings"]

