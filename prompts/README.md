# External LLM Coordination - Prompts Directory

This directory supports PR-based coordination with external LLMs (Master Planner, Codex, Claude Projects).

## Directory Structure

- **outbound/** - Requests TO external agents
- **inbound/** - Responses FROM external agents (via PR)
- **processed/** - Validated and accepted responses
- **latent/** - Deferred or ignored items

## Workflow

1. **Create request** in `outbound/` with complete instructions
2. **External agent** creates branch + response file in `inbound/`
3. **External agent** creates PR
4. **Review PR** and merge if acceptable
5. **Move to processed/** when implemented
6. **Move to latent/** if deferred

## File Naming Convention

```
YYYYMMDD_HHMMSS_<agent-id>-<topic>.md
```

Example: `20251030_163000_master-planner-architecture-review.md`

## See Also

- `AGENT.md` - Complete PR-based workflow documentation
- `OpenFlow-Playground/prompts/WORKFLOW.md` - Detailed protocol
