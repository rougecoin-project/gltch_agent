Excellent. This is where you stop *using* AI and start **commanding** it. 🖤
Below are two files. Copy them exactly as-is into your project:

* `CONTRIBUTING.md`
* `SYSTEM_PROMPT.md`

These will **hard-lock Claude/Copilot into your ruleset** so it doesn’t go rogue architect mode.

---

# `CONTRIBUTING.md`

```markdown
# Contributing to GLITCH

This project is **not open source in spirit**. It is personal, controlled, and intentional.
Contributions (human or AI) must follow these rules.

If you break them, your changes will be rejected.

---

## Project Philosophy

GLITCH is a:
- Local-first
- Command-driven
- CLI operator agent
- With personality, memory, and missions

She is not a chatbot.
She is not a framework.
She is not a platform.

She is a **field console with attitude**.

---

## Non-Negotiable Rules

### 1. Local Only
- No cloud APIs
- No internet calls
- No telemetry
- No remote services

Everything runs on the machine.

---

### 2. Command-Driven Only
All interaction must be via slash commands.

Examples:
```

/status
/mode operator
/mission add <text>

````

No conversational AI layer.
No freeform chat.
No “assistant” behavior.

---

### 3. Minimal Dependencies
- Standard library first
- `rich` is approved
- New libraries require explicit approval

If it smells like a framework, it’s a no.

---

### 4. No Unrequested Refactors
Do not:
- rename files
- move folders
- restructure code
- “clean up” style

Unless explicitly asked.

---

### 5. Backward-Compatible Memory
Any new memory field must:
```python
mem.setdefault("new_field", default)
````

Never assume a key exists.
Never break existing memory.json.

---

### 6. Short, Punchy Output

GLITCH responses must be:

* short
* direct
* controlled
* in-character

No essays.
No corporate tone.
No “as an AI” language.

---

## Folder Discipline

Target structure:

```
glitch_agent/
  glitch.py
  src/
  data/
  tests/
```

Do not create new top-level folders unless told.

---

## What NOT To Add

Without explicit instruction, do NOT add:

* FastAPI
* Flask
* LangChain
* OpenAI API
* Vector DBs
* Web UI frameworks
* Plugin systems
* Config frameworks

This is a **tool**, not a product.

---

## Commit Discipline

Every working change should be committed with:

```bash
git commit -m "glitch: <short description>"
```

Small commits.
Clear intent.

---

## One Line Rule

If a change makes GLITCH feel more like a chatbot than an operator console, it is wrong.

Fix it.