TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_pubmed",
            "description": (
                "Search PubMed for biomedical/clinical literature. Prefer this for "
                "clinical, health-services, adverse-event, and biomedical questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (PubMed search syntax supported)."},
                    "max_results": {"type": "integer", "description": "Max results to return (default 5, max 10).", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": (
                "Search arXiv for statistical, methodological, and operations-research "
                "literature. Prefer this for quantitative methodology questions "
                "(e.g. trial design statistics, optimization, forecasting)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "max_results": {"type": "integer", "description": "Max results to return (default 5, max 10).", "default": 5},
                    "category": {
                        "type": "string",
                        "description": "Optional arXiv category filter, e.g. 'stat.ME', 'stat.AP', 'math.OC'.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_from_index",
            "description": (
                "Semantically search over all documents gathered so far in this session "
                "(from prior search_pubmed/search_arxiv calls) to find the most relevant "
                "passages. Use this to re-rank or re-query after you've gathered some "
                "documents and want to focus on a refined question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Focused query to retrieve relevant passages for."},
                    "top_k": {"type": "integer", "description": "Number of passages to return (default 5).", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]
