# AI App Patterns from awesome-ai-apps Research

**Research Date:** May 25, 2026  
**Source:** [Arindam200/awesome-ai-apps](https://github.com/Arindam200/awesome-ai-apps)  
**Focus:** Plugin integration opportunities for one-shot-prompting

## Executive Summary

This document identifies three key architectural patterns from awesome-ai-apps that are directly applicable to the one-shot-prompting plugin. Each pattern addresses a distinct challenge in AI app development and offers proven implementation strategies.

---

## Pattern 1: Multi-Stage Workflow Orchestration

### Overview

**What it solves:** Complex, sequential tasks requiring different specialized agents at each stage, with output flowing linearly through refinement stages.

**Key characteristic:** Input → Stage A → Stage B → Stage C → Output, where each stage has distinct capabilities and responsibilities.

### Architecture

**Location:** `advance_ai_agents/deep_researcher_agent/`

**Components:**

```
Input Topic
    ↓
[Searcher Agent]    (web scraping + info extraction)
    ↓
[Analyst Agent]     (synthesis & interpretation)
    ↓
[Writer Agent]      (polish & formatting)
    ↓
Final Report
```

**Implementation Pattern:**

```python
from agno.agent import Agent
from agno.workflow import Workflow

class DeepResearcherAgent(Workflow):
    """Stages defined as agent properties"""
    searcher: Agent = Agent(
        tools=[ScrapeGraphTools()],
        instructions="Find and extract information from web..."
    )
    analyst: Agent = Agent(
        instructions="Synthesize and interpret findings..."
    )
    writer: Agent = Agent(
        instructions="Craft clear, structured report..."
    )

    def run(self, topic: str):
        """Linear orchestration: output feeds next input"""
        research = self.searcher.run(topic)
        analysis = self.analyst.run(research.content)
        report = self.writer.run(analysis.content, stream=True)
        return report
```

**Key Design Decisions:**

1. **State Passing:** Each stage's output becomes the next stage's input
2. **Tool Specialization:** Only searcher gets scraping tools; analyst/writer rely on reasoning
3. **Role Definition:** Distinct system prompts ensure agents stay in domain
4. **Streaming:** Final stage streams output for real-time feedback

### Applicability to one-shot-prompting

**High relevance** — The plugin's code generation workflow is naturally multi-stage:

| Plugin Stage | Mapping to Researcher Pattern | Tools |
|---|---|---|
| Scan & Extract | Searcher (extract domain from codebase) | Graph, scanner |
| Architecture (spec generation) | Analyst (synthesize into FK relationships) | Architect agent |
| Implementation | Writer (generate code) | Implementer + test-author agents |
| Verification | (post-write validation) | Verify, patch deterministic scripts |

**Existing Alignment:** The plugin already implements this pattern in `SKILL.md`:
- Architect agent (Sonnet) → spec.json
- Implementer/Test-Author (parallel; Haiku/Sonnet)
- Critic agent (Sonnet) → validation loop

### Implementation Suggestions

1. **Make stage dependencies explicit** in agent definitions (use `depends_on` metadata)
2. **Log stage transitions** with timing/cost for visibility
3. **Allow stage bypass** with `--skip-stage=analyst` flags for iteration
4. **Cache intermediate outputs** so re-running later stages is cheaper
5. **Consider parallel stages** where order-independence allows (e.g., parallelizing analysis subtasks)

### Example from awesome-ai-apps

- **Deep Researcher:** Searcher → Analyst → Writer for research reports
- **Due Diligence Agent:** Seed Crawler → 6 Parallel Specialists (Founders, Investors, Press, Financials, Tech Stack, Social) → Validator → Synthesis
  - More advanced: parallel specialists with `AG2.ConversableAgent` + `ThreadPoolExecutor`

### Links

- [Deep Researcher Agent](https://github.com/Arindam200/awesome-ai-apps/tree/main/advance_ai_agents/deep_researcher_agent)
- [Due Diligence Agent (AG2 + TinyFish)](https://github.com/Arindam200/awesome-ai-apps/tree/main/advance_ai_agents/due_diligence_agent)

---

## Pattern 2: MCP Agent Integration (External Tool Discovery & Registration)

### Overview

**What it solves:** Agents need to call tools not defined in their codebase — external APIs, specialized services, or domain-specific capabilities discovered at runtime.

**Key characteristic:** Agent receives MCP server connection → discovers available tools → uses tools via dynamic dispatch → no hardcoded tool list.

### Architecture

**Location:** `mcp_ai_agents/` (multiple examples: GitHub, custom email server, database, Docker)

**Components:**

```
Agent Request
    ↓
[MCPTools Wrapper]
    ↓ (stdio or HTTP)
[MCP Server Process]    (external: GitHub API, custom tool)
    ↓
[Tool Discovery]        (introspect available resources)
    ↓
[Dynamic Tool Dispatch] (map agent call to tool)
    ↓
Tool Response
```

**Implementation Pattern:**

```python
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_github_agent(query: str):
    # 1. Launch MCP server (Docker or subprocess)
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-e", "GITHUB_TOKEN", "ghcr.io/github/mcp-server-github"]
    )
    
    # 2. Create MCP client session
    async with stdio_client(server_params) as client:
        # 3. Discover available tools
        tools = MCPTools(mcp_client=client)
        
        # 4. Agent uses tools without knowing tool list
        agent = Agent(
            tools=[tools],  # Single wrapper; tools auto-discovered
            model=Nebius(id="deepseek-ai/DeepSeek-V3-0324"),
            instructions="Query GitHub repositories..."
        )
        
        response = await agent.run(query)
        return response
```

**Key Design Decisions:**

1. **Subprocess/Docker Launch:** MCP server runs as separate process (isolation + portability)
2. **Tool Introspection:** Agent queries server for available tools at runtime
3. **Error Handling:** Tool call failures gracefully degrade with context
4. **Authentication:** Pass credentials via environment variables (not in config)

### Custom MCP Server Example

**Scenario:** You want agents to send emails. Create an MCP server with `FastMCP`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("email")

@mcp.tool()
def send_email(receiver: str, subject: str, body: str) -> dict:
    """Send an email via SMTP"""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver
    msg.set_content(body)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, passkey)
        smtp.send_message(msg)
    return {"success": True}

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

Then use it in any agent:

```python
async with MCPServerStdio(params={
    "command": "python",
    "args": ["email-mcp/server.py"]
}) as mcp_server:
    agent = Agent(tools=[MCPTools(mcp_client=mcp_server)])
    await agent.run("Send an email to alice@example.com...")
```

### Applicability to one-shot-prompting

**High relevance** — Multiple integration points:

1. **GitHub Approval Integration (Path C, Gap 3):**
   - MCP server wraps GitHub API client
   - Agents dynamically discover: `check_approval_status()`, `request_review()`, `post_comment()`
   - No hardcoded GitHub tool list in plugin

2. **Code Validation MCP:**
   - Custom server wrapping `pytest`, `mypy`, `ruff`
   - Agents call `run_tests()`, `type_check()`, `lint_code()` dynamically
   - Decouples verification from agent code

3. **Domain-Specific Tools:**
   - Database MCP for schema introspection
   - Docker MCP for local test execution
   - File diff MCP for change visualization

### Implementation Suggestions

1. **Lazy-load MCP servers** (don't start until agent actually needs them)
2. **Cache tool inventory** across multiple agent calls to same server
3. **Version MCP servers** with tags (e.g., `github-mcp:v1.2`) for reproducibility
4. **Test MCP server discovery** in CI/CD to catch breakage early
5. **Document available tools** in a discoverable spec (JSON schema or markdown)

### Example from awesome-ai-apps

- **GitHub MCP Agent:** Queries repos, issues, PRs via GitHub MCP server
- **Custom Email MCP:** FastMCP-based email server with configure + send_email tools
- **Database MCP:** Introspect schema, run queries via MCP
- **Docker/E2B MCP:** Execute code in sandboxed environment via MCP
- **Couchbase MCP:** Query document DB without hardcoding client code

### Links

- [GitHub MCP Agent](https://github.com/Arindam200/awesome-ai-apps/tree/main/mcp_ai_agents/github_mcp_agent)
- [Custom Email MCP Server](https://github.com/Arindam200/awesome-ai-apps/tree/main/mcp_ai_agents/custom_mcp_server)
- [Agno MCP Tools Documentation](https://docs.agno.com/en/latest/tools/mcp)

---

## Pattern 3: Memory & Learning Agent (Cross-Project Knowledge Propagation)

### Overview

**What it solves:** Agents operating across multiple interactions/sessions need to remember user preferences, project patterns, past failures, and learned heuristics. Information must persist and inform future decisions.

**Key characteristic:** Agent reads memory before responding → updates memory after interaction → memory shapes future behavior.

### Architecture

**Location:** `memory_agents/agno_memory_agent/` (also: `arxiv_researcher_agent_with_memory`, `aws_strands_agent_with_memory`)

**Components:**

```
User Input
    ↓
[Memory Retrieval]         (load user memories)
    ↓
[Agent Response]           (conditioned on memories)
    ↓
[Memory Update]            (extract + store new facts)
    ↓
[Database]                 (SQLite, persistent)
```

**Implementation Pattern:**

```python
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.sqlite import SqliteStorage

# 1. Create memory database
memory = Memory(
    model=Nebius(id="deepseek-ai/DeepSeek-V3-0324"),
    db=SqliteMemoryDb(table_name="user_memories", db_file="agent.db")
)

# 2. Create storage for chat history
storage = SqliteStorage(table_name="agent_sessions", db_file="agent.db")

# 3. Initialize agent with memory enabled
agent = Agent(
    model=Nebius(id="deepseek-ai/DeepSeek-V3-0324"),
    memory=memory,                      # Enable memory
    enable_agentic_memory=True,         # Agent can update its own memories
    enable_user_memories=True,          # Auto-extract user preferences
    storage=storage,                    # Persist chat history
    add_history_to_messages=True,       # Include past context
    num_history_runs=3                  # Last 3 interactions
)

# 4. Use it (memory auto-managed)
agent.print_response(
    "My name is Alice and I prefer Python.",
    user_id="alice",
    stream=True
)

# Agent automatically extracts: "Alice prefers Python"
# Stored in database, available next conversation
```

**Memory Operation Modes:**

| Mode | What Happens | Use Case |
|---|---|---|
| `enable_agentic_memory=True` | Agent decides what to remember | Flexible, agent-driven |
| `enable_user_memories=True` | MemoryManager auto-extracts after response | Automatic, consistent |
| Both enabled | Agent + system both update memory | Comprehensive learning |

**Database Schema (SQLite):**

```
user_memories:
  id | user_id | memory_text | created_at | embedding
  
agent_sessions:
  id | user_id | messages | created_at | run_id
```

### Memory Types

1. **User Memories:** Facts about the user (preferences, constraints, history)
2. **Session History:** Past conversation turns (context window)
3. **Learned Heuristics:** Patterns the agent discovered (e.g., "user prefers test-first")

### Applicability to one-shot-prompting

**Very high relevance** — The plugin's curriculum & learning system aligns perfectly:

| Plugin Component | Memory Pattern Mapping | Database |
|---|---|---|
| `beads_curriculum.py` | User memories (failed patterns) | `.beads/curriculum.json` |
| Architect learned hints | Heuristics (FK patterns, common errors) | `.beads/*.json` |
| Cost tracking | Session history (generation costs) | `.beads/stats.json` |
| User preferences | User memories (budget, model, parallelism) | Plugin settings |

**Existing Alignment:** The plugin already uses `.beads/` as a memory store:
- `curriculum.json` → past failures + recommendations
- Cost tracking → inform budget decisions
- Pattern learning → suggest parallelization, constraint handling

### Implementation Suggestions

1. **Expand `.beads/` scope:**
   - Add `user_preferences.json` (inferred from past generations)
   - Add `learned_heuristics.json` (patterns agent discovered)
   - Version memories with timestamps for lifecycle management

2. **Agent-driven memory updates:**
   - Architect agent decides which spec patterns to remember
   - Implementer logs which bug patterns it fixed
   - Critic stores which test patterns worked

3. **Cross-project memory sharing:**
   - If user runs plugin on Project A, then Project B, share learned patterns
   - Remember which dependencies pair well (e.g., "FastAPI + Pydantic often need X")
   - Seed new projects with relevant past solutions

4. **Memory decay:**
   - Older memories have lower priority (heuristics change with versions)
   - Successful patterns boost confidence; failed patterns reduce it

5. **Memory introspection:**
   - `--show-memories` flag lists what plugin knows about user/project
   - `--clear-memories` flag resets learning for fresh start

### Example from awesome-ai-apps

**Agno Memory Agent:**
- User says: "My name is Arindam and I support Mohun Bagan."
- Agent extracts and stores: `{user_id: "arindam", preference: "Mohun Bagan"}`
- User asks later: "Tell me about me"
- Agent retrieves memory and provides context without re-asking

**Variant (Arxiv Researcher with Memory):**
- Remembers past queries + papers found
- Reuses search results when similar queries appear
- Tracks user's research interests over time
- Suggests related papers based on memory

### Links

- [Agno Memory Agent](https://github.com/Arindam200/awesome-ai-apps/tree/main/memory_agents/agno_memory_agent)
- [Arxiv Researcher with Memory](https://github.com/Arindam200/awesome-ai-apps/tree/main/memory_agents/arxiv_researcher_agent_with_memori)
- [AWS Strands Agent with Memory](https://github.com/Arindam200/awesome-ai-apps/tree/main/memory_agents/aws_strands_agent_with_memori)
- [Agno Memory Documentation](https://docs.agno.com/en/latest/memory)

---

## Integration Roadmap: Applying All Three Patterns

### Phase 1: Multi-Stage Orchestration (Current + Refinement)

**Timeline:** Already implemented; refinements in v3.7

- [ ] Make stage transitions explicit in agent definitions
- [ ] Add `--stage-skip` flag (e.g., `--skip-stage=verification` for faster iteration)
- [ ] Log stage costs for transparency

### Phase 2: MCP Agent Integration (Path C Expansion)

**Timeline:** Q3 2026

1. **GitHub Approval MCP Server** (extends Path C, Gap 3):
   - Wrap GitHub API in MCP server
   - Agents dynamically discover approval tools
   - Plugin calls MCP instead of direct API

2. **Code Validation MCP:**
   - Wrap pytest, mypy, ruff in MCP
   - Agents call validation dynamically
   - Decouples verification tools from agent logic

### Phase 3: Memory & Learning (Curriculum Enhancement)

**Timeline:** Q4 2026

1. **Expand `.beads/` scope:**
   - Add `user_preferences.json`
   - Add `learned_heuristics.json`
   - Version memory entries with timestamps

2. **Agent-driven memory updates:**
   - Architect logs spec patterns it discovered
   - Critic stores test patterns that worked
   - Plugin accumulates knowledge across projects

3. **Cross-project memory sharing:**
   - User runs plugin on multiple projects
   - Learned patterns transfer to new projects
   - Seed recommendations improve with usage

---

## Comparison: Pattern Characteristics

| Aspect | Multi-Stage | MCP Integration | Memory/Learning |
|---|---|---|---|
| **Complexity** | Medium (linear flow) | Medium (async I/O) | Medium (DB + embedding) |
| **Cost Impact** | High (multiple agent calls) | Medium (tool lookup) | Low (retrieval only) |
| **Failure Modes** | Stage A failure blocks B-C | Server startup failure | Memory staleness |
| **Best For** | Sequential refinement | Tool extension | Personalization |
| **Implementation Time** | 1-2 sprints | 1-2 sprints | 2-3 sprints |
| **User Visibility** | High (clear stages) | Low (transparent tool calls) | High (learning evident) |

---

## Conclusion

All three patterns are **immediately applicable** to one-shot-prompting:

1. **Multi-Stage Orchestration** (already 80% done) — Refine stage boundaries, add visibility
2. **MCP Integration** (strategic for Path C) — Enables tool extensibility without hardcoding
3. **Memory/Learning** (builds on `.beads/`) — Transforms one-shot from stateless to learning system

Combined, they form a **complete AI app architecture:** structured workflows + extensible tools + adaptive learning.

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-25  
**Next Review:** After Phase 1 refinements
