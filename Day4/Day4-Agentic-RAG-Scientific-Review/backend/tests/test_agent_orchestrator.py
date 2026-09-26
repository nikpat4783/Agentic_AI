import pytest

import app.agent.orchestrator as orchestrator


class FakeGroqClient:
    """Scripts a sequence of chat_completion responses for tool_choice='auto',
    and a separate response for the forced tool_choice='none' call."""

    def __init__(self, api_key, auto_responses=None, forced_response=None):
        self._auto_responses = list(auto_responses or [])
        self._forced_response = forced_response
        self.calls = []

    async def chat_completion(self, model, messages, tools=None, tool_choice="auto"):
        self.calls.append(tool_choice)
        if tool_choice == "none":
            return self._forced_response
        return self._auto_responses.pop(0)


def _tool_call_message(name: str, args: str, call_id: str = "call_1") -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": call_id, "function": {"name": name, "arguments": args}}],
    }


def _final_message(content: str) -> dict:
    return {"role": "assistant", "content": content, "tool_calls": None}


async def _collect_events(gen):
    events = []
    async for event in gen:
        events.append(event)
    return events


@pytest.fixture(autouse=True)
def stub_pubmed(monkeypatch):
    call_count = {"n": 0}

    async def fake_search_pubmed(query, max_results=5):
        call_count["n"] += 1
        return {
            "results": [
                {
                    "pmid": "12345678",
                    "title": "Hepatotoxicity signals paper",
                    "abstract": "Some abstract text.",
                    "authors": ["Jane Smith"],
                    "journal": "J. Safety",
                    "year": "2024",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                }
            ]
        }

    monkeypatch.setattr(orchestrator, "search_pubmed", fake_search_pubmed)
    monkeypatch.setattr(orchestrator, "index_documents", lambda *a, **k: 1)
    return call_count


@pytest.mark.asyncio
async def test_tool_is_dispatched_once_and_final_citations_match(monkeypatch, stub_pubmed):
    tool_call_msg = _tool_call_message("search_pubmed", '{"query": "hepatotoxicity"}')
    final_msg = _final_message(
        "There is an elevated hepatotoxicity signal [PMID:12345678]."
    )

    fake_client = FakeGroqClient(api_key="fake", auto_responses=[tool_call_msg, final_msg])
    monkeypatch.setattr(orchestrator, "GroqClient", lambda api_key: fake_client)

    events = await _collect_events(
        orchestrator.run_agentic_rag(
            question="What are hepatotoxicity signals?",
            domain_id="pharmacovigilance",
            model="test/model",
            api_key="fake-key",
            session_id="sess-1",
        )
    )

    assert stub_pubmed["n"] == 1  # tool dispatched exactly once

    event_types = [e["type"] for e in events]
    assert event_types == ["tool_call", "tool_result", "final"]

    final_event = events[-1]
    assert final_event["incomplete"] is False
    assert final_event["citations"] == [
        {"id": "PMID:12345678", "title": "Hepatotoxicity signals paper", "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"}
    ]


@pytest.mark.asyncio
async def test_max_iterations_forces_incomplete_final_answer(monkeypatch, stub_pubmed):
    monkeypatch.setattr(orchestrator.settings, "max_agent_iterations", 2)

    tool_call_msg = _tool_call_message("search_pubmed", '{"query": "hepatotoxicity"}')
    forced_final = _final_message("Best-effort answer given limited evidence [PMID:12345678].")

    fake_client = FakeGroqClient(
        api_key="fake",
        auto_responses=[tool_call_msg, tool_call_msg],
        forced_response=forced_final,
    )
    monkeypatch.setattr(orchestrator, "GroqClient", lambda api_key: fake_client)

    events = await _collect_events(
        orchestrator.run_agentic_rag(
            question="What are hepatotoxicity signals?",
            domain_id="pharmacovigilance",
            model="test/model",
            api_key="fake-key",
            session_id="sess-2",
        )
    )

    final_event = events[-1]
    assert final_event["type"] == "final"
    assert final_event["incomplete"] is True
    assert "none" in fake_client.calls  # the forced termination call was made


@pytest.mark.asyncio
async def test_tool_failure_becomes_error_message_not_a_crash(monkeypatch):
    async def failing_search_pubmed(query, max_results=5):
        raise RuntimeError("NCBI is down")

    monkeypatch.setattr(orchestrator, "search_pubmed", failing_search_pubmed)

    tool_call_msg = _tool_call_message("search_pubmed", '{"query": "hepatotoxicity"}')
    final_msg = _final_message("I could not find sufficient evidence.")

    fake_client = FakeGroqClient(api_key="fake", auto_responses=[tool_call_msg, final_msg])
    monkeypatch.setattr(orchestrator, "GroqClient", lambda api_key: fake_client)

    events = await _collect_events(
        orchestrator.run_agentic_rag(
            question="What are hepatotoxicity signals?",
            domain_id="pharmacovigilance",
            model="test/model",
            api_key="fake-key",
            session_id="sess-3",
        )
    )

    tool_result_event = events[1]
    assert tool_result_event["type"] == "tool_result"
    assert "NCBI is down" in tool_result_event["summary"]
    assert events[-1]["type"] == "final"
