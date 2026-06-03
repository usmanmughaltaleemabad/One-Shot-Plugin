# Privacy Policy

**Effective Date:** June 3, 2026

## Data Collection

The One-Shot Prompting plugin **does not collect, store, or sell any user data**, and makes **no external network calls by default**.

### What the Plugin Does
- Processes user prompts locally within Claude Code
- Generates code based on your input
- Does not send your prompts to external services
- Does not store chat history or generated code
- Does not track usage or analytics

### Network Behavior
By default the plugin makes **no external API calls, HTTP requests, or data transmissions** beyond your local Claude Code instance.

**One opt-in exception:** if you explicitly pass `--require-approval-webhook=URL`, the approval-gate stage POSTs a generation summary (including code diffs) to the webhook URL **you** configure, so a human/system can approve changes before they are wired in. This is **disabled by default** and only ever sends data to an endpoint you supply. No other network egress exists.

### No Telemetry
We do not collect:
- Prompts you write
- Code we generate
- Usage statistics
- Device information
- Location data
- Any identifying information

### Transparency
All plugin code is open-source on GitHub. You can audit exactly what the plugin does:
https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

### Data in Claude Code
Claude Code itself may collect usage data per Anthropic's policies. This plugin does not add any additional data collection beyond Claude Code's standard behavior.

### Questions?
If you have privacy questions, open an issue on GitHub:
https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues

---

**Last Updated:** June 3, 2026
