import json
import re
from collections.abc import AsyncIterator
from typing import Any

from app.agent.groq_client import GroqClient, GroqError
from app.agent.prompts import build_system_prompt
from app.agent.tools.arxiv_tool import search_arxiv
from app.agent.tools.pubmed_tool import search_pubmed
from app.agent.tools.schemas import TOOL_SCHEMAS
from app.agent.tools.vector_tool import retrieve_from_index
from app.config import settings
from app.domains.config import get_domain
from app.observability import agent_loop_iterations, tracer
from app.rag.indexer import index_documents

CITATION_PATTERN = re.compile(r"\[(PMID|arXiv):([\w.]+)\]")


async def run_agentic_rag(
    question: str,
    domain_id: str,
    model: str,
    api_key: str,
    session_id: str,
) -> AsyncIterator[dict]:
    domain = get_domain(domain_id)
    if domain is None:
        yield {"type": "error", "message": f"Unknown domain: {domain_id}"}
        return

    client = GroqClient(api_key)
    messages: list[dict] = [
        {"role": "system", "content": build_system_prompt(domain)},
        {"role": "user", "content": question},
    ]
    source_registry: dict[str, dict] = {}
    max_iterations = settings.max_agent_iterations
    iterations_used = 0

    try:
        for iteration in range(max_iterations):
            iterations_used = iteration + 1
            message = await client.chat_completion(model, messages, tools=TOOL_SCHEMAS, tool_choice="auto")
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                answer = message.get("content") or ""
                agent_loop_iterations.record(iterations_used, {"domain.id": domain_id})
                yield _final_event(answer, source_registry, incomplete=False)
                return

            messages.append(
                {"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls}
            )

            for tool_call in tool_calls:
                fn = tool_call["function"]
                name = fn["name"]
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}

                yield {"type": "tool_call", "tool": name, "args": args}

                with tracer.start_as_current_span(
                    "agent.tool_iteration",
                    attributes={"tool.name": name, "domain.id": domain_id, "iteration": iteration},
                ):
                    result = await _dispatch_tool(name, args, session_id, domain_id, source_registry)

                yield {"type": "tool_result", "tool": name, "summary": _summarize_result(name, result)}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result),
                    }
                )

        # max_iterations exhausted with tool calls still happening: force a final answer
        final_message = await client.chat_completion(model, messages, tools=TOOL_SCHEMAS, tool_choice="none")
        answer = final_message.get("content") or "I was unable to reach a complete answer within the step budget."
        agent_loop_iterations.record(iterations_used, {"domain.id": domain_id})
        yield _final_event(answer, source_registry, incomplete=True)

    except GroqError as exc:
        agent_loop_iterations.record(iterations_used, {"domain.id": domain_id})
        yield {"type": "error", "message": str(exc)}


async def _dispatch_tool(
    name: str,
    args: dict[str, Any],
    session_id: str,
    domain_id: str,
    source_registry: dict[str, dict],
) -> dict:
    try:
        if name == "search_pubmed":
            result = await search_pubmed(args.get("query", ""), args.get("max_results", 5))
            _index_pubmed_results(result, session_id, domain_id, source_registry)
            return result
        if name == "search_arxiv":
            result = await search_arxiv(args.get("query", ""), args.get("max_results", 5), args.get("category"))
            _index_arxiv_results(result, session_id, domain_id, source_registry)
            return result
        if name == "retrieve_from_index":
            return await retrieve_from_index(session_id, domain_id, args.get("query", ""), args.get("top_k", 5))
        return {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        return {"error": f"Tool '{name}' failed: {exc}"}


def _index_pubmed_results(result: dict, session_id: str, domain_id: str, source_registry: dict[str, dict]) -> None:
    docs = []
    for item in result.get("results", []):
        source_id = f"PMID:{item['pmid']}"
        source_registry[source_id] = {"title": item["title"], "url": item["url"], "id": item["pmid"]}
        docs.append(
            {
                "source_id": source_id,
                "text": f"{item['title']}\n{item['abstract']}",
                "metadata": {"source_id": source_id, "title": item["title"], "url": item["url"]},
            }
        )
    if docs:
        index_documents(session_id, domain_id, docs)


def _index_arxiv_results(result: dict, session_id: str, domain_id: str, source_registry: dict[str, dict]) -> None:
    docs = []
    for item in result.get("results", []):
        source_id = f"arXiv:{item['arxiv_id']}"
        source_registry[source_id] = {"title": item["title"], "url": item["url"], "id": item["arxiv_id"]}
        docs.append(
            {
                "source_id": source_id,
                "text": f"{item['title']}\n{item['abstract']}",
                "metadata": {"source_id": source_id, "title": item["title"], "url": item["url"]},
            }
        )
    if docs:
        index_documents(session_id, domain_id, docs)


def _summarize_result(tool_name: str, result: dict) -> str:
    if "error" in result:
        return result["error"]
    count = len(result.get("results", []))
    if tool_name == "search_pubmed":
        return f"Found {count} PubMed article(s)."
    if tool_name == "search_arxiv":
        return f"Found {count} arXiv paper(s)."
    if tool_name == "retrieve_from_index":
        return f"Retrieved {count} passage(s) from the session index."
    return f"Returned {count} result(s)."


def _final_event(answer: str, source_registry: dict[str, dict], incomplete: bool) -> dict:
    cited_ids = {f"{kind}:{sid}" for kind, sid in CITATION_PATTERN.findall(answer)}
    citations = [
        {"id": source_id, "title": info["title"], "url": info["url"]}
        for source_id, info in source_registry.items()
        if source_id in cited_ids
    ]
    return {"type": "final", "answer": answer, "citations": citations, "incomplete": incomplete}
