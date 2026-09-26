# Graph Report - Day4_Claude_Code  (2026-09-19)

## Corpus Check
- Corpus is ~1,092 words - fits in a single context window. You may not need a graph.

## Summary
- 52 nodes · 61 edges · 5 communities
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.82)
- Token cost: 45,999 input · 0 output

## Community Hubs (Navigation)
- Frontend DOM Components
- Documentation & Architecture
- Package Configuration
- Test Suite
- Core Calculator Functions

## God Nodes (most connected - your core abstractions)
1. `scripts` - 4 edges
2. `renderResults()` - 4 edges
3. `Backend Agent Specification` - 4 edges
4. `SIP Calculator Frontend HTML` - 4 edges
5. `loadSipResults()` - 3 edges
6. `SIP Calculator Application` - 3 edges
7. `Form Validation Pattern` - 3 edges
8. `express` - 2 edges
9. `formatCurrency()` - 2 edges
10. `calculateSipValue()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `SIP Calculator Frontend HTML` --implements--> `Form Validation Pattern`  [INFERRED]
  index.html → .claude/agents/backend-agent.md
- `SIP Calculator Frontend HTML` --implements--> `SIP Calculator Application`  [EXTRACTED]
  index.html → .claude/agents/backend-agent.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **SIP Calculator System Components** — _claude_agents_backend_agent, index, server, script, styles [EXTRACTED 0.95]

## Communities (5 total, 0 thin omitted)

### Community 0 - "Frontend DOM Components"
Cohesion: 0.13
Nodes (14): annualStepUpInput, currencyFormatter, estimatedGainsEl, expectedReturnInput, form, initial, investmentYearsInput, maturityAmountEl (+6 more)

### Community 1 - "Documentation & Architecture"
Cohesion: 0.21
Nodes (12): Backend Agent Specification, Express.js Framework, Form Validation Pattern, SIP Calculator Frontend HTML, JSON Error Handling Pattern, Node.js Runtime, ref_path, app (+4 more)

### Community 2 - "Package Configuration"
Cohesion: 0.17
Nodes (11): dependencies, express, description, main, name, scripts, dev, start (+3 more)

### Community 3 - "Test Suite"
Cohesion: 0.29
Nodes (6): ref_node_assert, ref_node_test, calculateSipValue(), assert, { calculateSipValue }, test

### Community 4 - "Core Calculator Functions"
Cohesion: 0.40
Nodes (5): calculateSipValue(), formatCurrency(), loadSipResults(), renderResults(), updateSummary()

## Knowledge Gaps
- **31 isolated node(s):** `name`, `version`, `description`, `main`, `start` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 34 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `express` connect `Package Configuration` to `Documentation & Architecture`?**
  _High betweenness centrality (0.345) - this node is a cross-community bridge._
- **Why does `SIP Calculator Frontend HTML` connect `Documentation & Architecture` to `Frontend DOM Components`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **What connects `name`, `version`, `description` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend DOM Components` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._