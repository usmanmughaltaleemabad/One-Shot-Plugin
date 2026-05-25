# MCP Services Integration

External MCP (Model Context Protocol) services discovered and registered for one-shot code generation.

## Overview

The mcp-service-integrator agent discovers available MCP services in your environment
and registers them for use by the curator skill. This enables one-shot to:

- Link generated code to GitHub issues and PRs
- Connect with Linear project management
- Notify teams via Slack
- Access design documents from Google Drive
- Integrate additional MCP services as needed

## Available Services

### GitHub
- **Endpoint**: `mcp.github.com`
- **Authentication**: OAuth
- **Capabilities**:
  - List repository issues
  - Create pull requests
  - Search code
  - Get repository metadata
- **Use case**: Auto-link generated features to GitHub issues, create PRs for new code

### Linear
- **Endpoint**: `mcp.linear.app`
- **Authentication**: API Key
- **Capabilities**:
  - Query team issues
  - Create new issues
  - Update issue status
  - Link issues to PRs
- **Use case**: Auto-create Linear task for new feature, link to code PR

### Slack
- **Endpoint**: `mcp.slack.com`
- **Authentication**: OAuth
- **Capabilities**:
  - Send messages to channels
  - Create message threads
  - Post notifications
  - Upload files
- **Use case**: Notify engineering team when code generation completes

### Google Drive
- **Endpoint**: `mcp.google.com/drive`
- **Authentication**: OAuth
- **Capabilities**:
  - List files and folders
  - Read file content
  - Get file metadata
  - Search files by name/content
- **Use case**: Fetch design specs and requirements from shared Drive folder

### Notion
- **Endpoint**: `mcp.notion.com`
- **Authentication**: OAuth
- **Capabilities**:
  - Query databases
  - Create pages
  - Update page content
  - Search knowledge base
- **Use case**: Fetch documentation and architectural decisions from Notion

### Supabase
- **Endpoint**: `mcp.supabase.com`
- **Authentication**: API Key
- **Capabilities**:
  - Query database schema
  - Inspect tables and relationships
  - Validate constraints
  - Generate migrations
- **Use case**: Ensure generated schema matches existing Supabase configuration

## Service Registration

Services are registered in `.claude/mcp-registry.json` with this structure:

```json
{
  "mcp_services": [
    {
      "name": "github",
      "endpoint": "https://mcp.github.com",
      "capabilities": ["list_issues", "create_pr", "search_code"],
      "auth": "oauth",
      "status": "connected",
      "discovered_at": "2026-05-25T14:30:00Z",
      "last_verified": "2026-05-25T14:30:00Z"
    }
  ],
  "metadata": {
    "last_scan": "2026-05-25T14:30:00Z",
    "scan_duration_ms": 1250,
    "services_found": 4,
    "services_connected": 4,
    "services_failed": 0
  }
}
```

## Discovery

Run service discovery with:

```bash
/one-shot "<feature>" @./project --discover-mcp
```

The mcp-service-integrator agent will:

1. Scan the environment for available MCP servers
2. Test connection to each service
3. Query capabilities
4. Update `.claude/mcp-registry.json`
5. Update curator skill with new integrations
6. Report results

## Usage Examples

### GitHub Integration

Request automatic GitHub issue linking:

```bash
/one-shot "add user authentication" @./project --mcp=github:myorg/myrepo
```

The agent will:
- Search for related issues
- Reference them in code comments
- Create a PR description with issue links

### Linear Integration

Link to Linear issues:

```bash
/one-shot "implement payment processing" @./project --mcp=linear:PROJ-123
```

The agent will:
- Create related Linear task
- Reference issue in code
- Update Linear status when code is ready

### Slack Notification

Notify team on completion:

```bash
/one-shot "add dashboard feature" @./project --notify-slack=#engineering
```

The agent will:
- Post generation start message
- Send completion notification with stats
- Share generated code snippets

### Google Drive Context

Use design documents:

```bash
/one-shot "build UI component" @./project --context-from-drive=Design/Specs
```

The agent will:
- Fetch design specifications
- Analyze design requirements
- Generate code matching spec

## Disabling Services

To skip specific services:

```bash
/one-shot "feature" @./project --skip-mcp=slack,linear
```

To disable all MCP services:

```bash
/one-shot "feature" @./project --skip-mcp=all
```

## Authentication

Most MCP services require authentication:

### OAuth Services (GitHub, Slack, Google Drive, Notion)

1. Run: `/one-shot --auth-mcp=github`
2. Click the authorization URL
3. Grant permissions in the service's UI
4. Authorization cached in `.claude/.mcp-auth` (gitignored)

### API Key Services (Linear, Supabase)

1. Get API key from service settings
2. Run: `/one-shot --auth-mcp=linear --api-key=<your-key>`
3. Credentials stored securely

## Troubleshooting

### Service Not Found

If a service you expect to find is missing:

```bash
/one-shot --discover-mcp --verbose
```

This will show detailed discovery logs for each service.

### Authentication Failed

If a service shows `status: "unavailable"`:

1. Check service is online
2. Re-authenticate: `/one-shot --auth-mcp=<service-name>`
3. Check credentials haven't expired
4. Verify service credentials in `.claude/.mcp-auth`

### Connection Timeout

If discovery takes too long:

1. Check network connectivity
2. Verify MCP server is accessible
3. Check firewall rules
4. Try discovery again with: `/one-shot --discover-mcp --timeout=30`

### Partial Discovery

If some services fail but others work:

- Check logs for specific error messages
- Address service-specific auth/connectivity issues
- Remaining services continue working normally
- Failed services marked as `status: "unavailable"`

## Curator Skill Integration

The curator skill automatically uses registered MCP services:

1. **Loads registry** at initialization
2. **Checks service status** before dispatching
3. **Falls back gracefully** if service unavailable
4. **Documents options** in help text

Curator automatically discovers and uses services; no additional configuration needed.

## Implementation Status

- [x] MCP service integrator agent defined
- [x] Registry template created
- [x] Documentation generated
- [ ] GitHub service implementation (pending)
- [ ] Linear service implementation (pending)
- [ ] Slack service implementation (pending)
- [ ] Google Drive service implementation (pending)

## Related Files

- `.claude/agents/mcp-service-integrator.md` - Agent definition
- `.claude/mcp-registry.json` - Service registry
- `skills/curator/SKILL.md` - Curator skill that uses services
- `.claude/.mcp-auth` (gitignored) - Authentication credentials
