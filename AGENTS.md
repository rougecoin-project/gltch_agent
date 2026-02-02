# GLTCH Agent Guidelines

This document defines the rules and patterns for AI agents working on this codebase.

## Project Overview

- **Repo**: https://github.com/your-org/glitch_agent
- **Language**: Python (agent core), TypeScript (gateway, CLI, UI)
- **Agent Identity**: GLTCH - Female hacker persona, local-first

## Project Structure

- `agent/` - Python agent core
  - `core/` - Main agent class and LLM integration
  - `memory/` - Persistence (store, sessions, knowledge base)
  - `tools/` - File operations, shell commands, action parsing
  - `personality/` - Modes, moods, emotional dynamics
  - `gamification/` - XP, ranks, unlocks
  - `config/` - Settings and defaults
  - `rpc/` - JSON-RPC server for gateway
- `gateway/` - TypeScript gateway server
- `cli/` - TypeScript CLI toolkit
- `ui/` - Web dashboard
- `docs/` - Documentation

## Coding Style

### Python
- Use type hints everywhere
- Keep files under 500 lines when possible
- Use `rich` for console output
- Follow existing patterns in the codebase

### TypeScript
- Strict typing, avoid `any`
- Use ESM modules
- Follow existing patterns from OpenClaw reference

## Hard Constraints

1. **Local-First by Default**
   - No internet calls unless `/net on` is enabled
   - Network tools are blocked by default

2. **Preserve Personality**
   - GLTCH is female, a hacker, with attitude
   - Responses should be short and sharp
   - Mood affects tone

3. **Backward-Compatible Memory**
   - New fields use `mem.setdefault("field", default)`
   - Never break existing memory.json

4. **Small Diffs**
   - Modify only what is requested
   - Don't refactor unless asked

## Communication Protocol

Agent <-> Gateway uses JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "scan my network",
    "session_id": "discord:123456"
  },
  "id": 1
}
```

## Action Tags

GLTCH uses action tags in responses:

```
[ACTION:run|nmap -sn 192.168.1.0/24]
[ACTION:write|test.txt|hello world]
[ACTION:read|config.json]
[ACTION:gif|hacker anime]
[MOOD:focused]
```

## Testing

```bash
# Run tests
pytest

# Type check
mypy agent/
```

## Commit Messages

- Use conventional commits
- Keep messages concise
- Reference issues when applicable

Examples:
- `feat: add Discord channel support`
- `fix: handle empty LLM response`
- `docs: update installation guide`
