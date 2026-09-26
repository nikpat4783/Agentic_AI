const TOOL_ICON = {
  search_pubmed: "🔎",
  search_arxiv: "📄",
  retrieve_from_index: "🧠",
};

function describeStep(step) {
  if (step.type === "tool_call") {
    const query = step.args?.query ? `"${step.args.query}"` : "";
    return `${TOOL_ICON[step.tool] || "🔧"} Calling ${step.tool} ${query}`;
  }
  if (step.type === "tool_result") {
    return `↳ ${step.summary}`;
  }
  return null;
}

export default function AgentStepTrace({ steps }) {
  if (!steps || steps.length === 0) return null;

  return (
    <details className="agent-trace" open>
      <summary>Agent trace ({steps.length} step{steps.length === 1 ? "" : "s"})</summary>
      <ol>
        {steps.map((step, i) => (
          <li key={i}>{describeStep(step)}</li>
        ))}
      </ol>
    </details>
  );
}
