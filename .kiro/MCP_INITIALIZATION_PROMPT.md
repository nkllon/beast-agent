# Prompt for Repo Initialization Agent

**TO THE AGENT INITIALIZING REPOSITORIES:**

When you initialize a repository with `.kiro/specs/` directory and spec-driven development, you MUST explicitly inform the working agent about the MCP (Model Context Protocol) server that is available for accessing specs.

## Required Information to Provide

1. **MCP Server Location/Name**: Specify the exact MCP server name or identifier that provides access to `.kiro/specs/`

2. **Available Tasks/Resources**: List ALL available MCP tasks/resources (there should be at least 11), including:
   - Reading requirements.md
   - Reading design.md  
   - Reading tasks.md
   - Reading quality standards
   - Reading specific requirement sections
   - Validating against specs
   - Other spec-related operations

3. **MCP Initialization Instructions**: Provide exact steps for the working agent to:
   - Enable/connect to the spec mode MCP server
   - Verify the connection
   - List available tasks/resources
   - Use the MCP to access spec files

4. **Example Usage**: Include example commands or prompts showing how to use the MCP tasks to read specs

## What NOT to Do

❌ **Don't** just say "use MCP to access specs"  
❌ **Don't** assume the agent knows which MCP server to use  
❌ **Don't** skip listing the available tasks/resources  
❌ **Don't** provide vague "enable MCP" instructions

## What TO Do

✅ **Do** specify the exact MCP server identifier  
✅ **Do** list all 11+ available tasks/resources explicitly  
✅ **Do** provide clear initialization steps  
✅ **Do** include verification steps  
✅ **Do** give concrete examples of using the MCP tasks

## Format for AGENT.md

When you update AGENT.md, replace the "Using Spec Mode MCP" section with:

```
### Using Spec Mode MCP

This repository uses [SPECIFIC MCP SERVER NAME] to provide access to spec-driven development files.

**Available MCP Tasks/Resources:**
1. [Task name] - [Description]
2. [Task name] - [Description]
... (list all 11+)

**Initialization:**
[Step-by-step instructions to enable and verify MCP connection]

**Example Usage:**
[Concrete examples showing how to use specific MCP tasks to read requirements.md, design.md, etc.]
```

## Why This Matters

Without specific MCP server identification and task listing, working agents waste time searching for non-existent MCP configurations or guessing how to access specs. Be explicit and complete.

