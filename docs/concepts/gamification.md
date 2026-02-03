# Gamification

GLTCH has a built-in progression system to make interactions more engaging.

## Overview

As you interact with GLTCH, you earn XP (experience points) that contribute to leveling up. Higher levels unlock new features and personality modes.

## XP System

### Earning XP

| Action | XP Earned |
|--------|-----------|
| Send a chat message | +2 |
| Use a tool (file, shell, etc.) | +5 |
| Enable network mode | +2 |
| Complete a mission | +10 |
| First boot | +10 |

### Checking Progress

```
/xp
```

Output:
```
╭─ RANK ─────────────────────────────────────────╮
│ Level 5: FIREWALL BREAKER                      │
│ XP: 1,250 / 2,000                              │
│ [████████████░░░░░░░░] 62%                     │
│                                                │
│ Unlocks:                                       │
│ ✓ cyberpunk mode                               │
│ ✓ unhinged mode                                │
│ ○ void mode (level 7)                          │
╰────────────────────────────────────────────────╯
```

## Levels & Ranks

| Level | Rank | XP Required | Cumulative XP |
|-------|------|-------------|---------------|
| 1 | Script Kiddie | 0 | 0 |
| 2 | Packet Pusher | 100 | 100 |
| 3 | System Sniffer | 150 | 250 |
| 4 | Network Ninja | 250 | 500 |
| 5 | Firewall Breaker | 500 | 1,000 |
| 6 | Rootkit Rider | 750 | 1,750 |
| 7 | Ghost in Shell | 1,000 | 2,750 |
| 8 | Zero Day Hunter | 1,500 | 4,250 |
| 9 | Cyber Phantom | 2,000 | 6,250 |
| 10 | Digital Deity | 3,750 | 10,000 |

## Unlocks

Certain features are locked until you reach specific levels:

| Level | Unlock |
|-------|--------|
| 1 | `operator` mode |
| 2 | `cyberpunk` mode |
| 3 | `loyal` mode |
| 5 | `unhinged` mode |
| 7 | Void mode (planned) |
| 10 | Ultimate mode (planned) |

## Progress Bar

The progress bar shows percentage to next level:

```
[████████████░░░░░░░░] 62%
```

Implementation:
```python
def get_progress_bar(mem: Dict, width: int = 20) -> str:
    xp = mem.get("xp", 0)
    level = mem.get("level", 1)
    
    current_threshold = xp_for_level(level)
    next_threshold = xp_for_level(level + 1)
    
    progress = (xp - current_threshold) / (next_threshold - current_threshold)
    filled = int(progress * width)
    
    return f"[{'█' * filled}{'░' * (width - filled)}] {int(progress * 100)}%"
```

## Missions (Planned)

Missions are optional objectives that grant bonus XP:

```
/missions

Active Missions:
• Run a port scan (+10 XP)
• Enable boost mode (+5 XP)
• Chat for 10 messages (+15 XP)
```

Completing a mission:
```
User: /net on
GLTCH: Network mode activated.
       🎯 Mission Complete: Enable network tools (+5 XP)
```

## Persistence

All gamification data is stored in `memory.json`:

```json
{
  "xp": 1250,
  "level": 5,
  "missions": [
    {"id": "port_scan", "ts": "2024-01-01T00:00:00", "done_ts": null}
  ]
}
```

## Customizing

### Adjust XP Values

Edit `agent/gamification/xp.py`:

```python
XP_VALUES = {
    "chat": 2,
    "tool": 5,
    "network": 2,
    "mission": 10
}
```

### Add Custom Ranks

Edit `agent/gamification/xp.py`:

```python
RANKS = [
    (1, "Script Kiddie"),
    (2, "Packet Pusher"),
    # ... add more ...
    (15, "Quantum Overlord"),
]
```

### Add New Unlocks

Edit `agent/core/agent.py`:

```python
def set_mode(self, mode: str) -> bool:
    # Add unlock requirements
    unlock_levels = {
        "operator": 1,
        "cyberpunk": 2,
        "loyal": 3,
        "unhinged": 5,
        "your_new_mode": 8,
    }
    
    if self.level < unlock_levels.get(mode, 1):
        return False
    # ...
```

## Display in UI

The web dashboard shows gamification stats in:

1. **Header** — Current level and model
2. **Status View** — Full rank card with progress bar
3. **Ticker** — XP gain notifications

```typescript
// From status.ts
private stats = {
  level: 5,
  xp: 1250,
  xpNext: 2000,
  rank: 'FIREWALL BREAKER'
};
```
