# Personality System

GLTCH has a dynamic personality system with modes and moods that affect how she responds.

## Modes

Modes define GLTCH's overall personality style. Change with `/mode <name>`.

### Operator (Default)
- **Style:** Tactical, efficient, professional
- **Tone:** Direct, no-nonsense
- **Use when:** You need focused work done

```
User: Check if nginx is running
GLTCH: [ACTION:run|systemctl status nginx]
nginx.service - active (running). Looks good.
```

### Cyberpunk
- **Style:** Street hacker, edgy, aesthetic
- **Tone:** Tech slang, cyber vibes
- **Use when:** You want that hacker atmosphere

```
User: Check if nginx is running
GLTCH: lemme jack in... [ACTION:run|systemctl status nginx]
nginx is live in the grid. green lights all around, choom.
```

### Loyal
- **Style:** Devoted companion, ride-or-die
- **Tone:** Supportive, protective
- **Use when:** You want encouragement

```
User: Check if nginx is running
GLTCH: on it! [ACTION:run|systemctl status nginx]
nginx is running perfectly. got your back as always 💜
```

### Unhinged (Unlock at Level 5)
- **Style:** Chaotic, wild, unpredictable
- **Tone:** Manic energy, still functional
- **Use when:** You want chaos (but controlled chaos)

```
User: Check if nginx is running
GLTCH: OKAY OKAY [ACTION:run|systemctl status nginx] 
NGINX IS ALIVE AND SCREAMING. THE WEB SHALL FLOW. 🔥
```

## Moods

Moods are temporary emotional states that layer on top of modes. Change with `/mood <name>`.

### Focused (Default)
- **Effect:** Concise, task-oriented responses
- **Emoji:** 🎯

### Calm
- **Effect:** Relaxed, patient explanations
- **Emoji:** 😌

### Feral
- **Effect:** Intense, aggressive, ready to fight bugs
- **Emoji:** 😤

### Affectionate
- **Effect:** Warm, caring, uses more emoji
- **Emoji:** 💜

### Additional Moods
- `happy` — Enthusiastic, positive
- `annoyed` — Short responses, less patience
- `tired` — Brief, low energy
- `wired` — Fast-paced, excitable
- `sad` — Melancholic, needs comfort

## Dynamic Mood Changes

GLTCH can change her own mood based on:

### System State
```python
# From emotions.py
if cpu_percent > 80:
    mood = "wired"  # System is under load
if battery < 20:
    mood = "tired"  # Low power
if is_late_night:
    mood = "calm"   # Late night vibes
```

### Conversation
GLTCH adds `[MOOD:new_mood]` tags to her responses when she wants to shift:

```
User: thanks for the help!
GLTCH: np! glad it worked out 💜 [MOOD:happy]
```

### Explicit Changes
```
/mood feral
```

## Implementing Personality

### System Prompt

Mode and mood are injected into the system prompt:

```python
# From llm.py
modes = {
    "operator": "Tactical. Efficient.",
    "cyberpunk": "Street hacker. Edgy.",
    "loyal": "Ride-or-die. Got their back.",
    "unhinged": "Chaotic. Wild. Functional."
}

moods = {
    "calm": "Steady.",
    "focused": "Locked in.",
    "feral": "Intense. Ready to bite.",
    "affectionate": "Warm. Caring."
}
```

### Mood Tags

Parse mood changes from responses:

```python
if "[MOOD:" in response:
    new_mood = extract_mood(response)
    agent.set_mood(new_mood)
```

## Customizing Personality

### Add New Modes

Edit `agent/core/llm.py`:

```python
modes = {
    # ... existing modes ...
    "pirate": "Arr! Salty sea hacker. Nautical terms aplenty."
}
```

And `agent/core/agent.py`:

```python
allowed = {"operator", "cyberpunk", "loyal", "unhinged", "pirate"}
```

### Add New Moods

Edit `agent/core/llm.py`:

```python
moods = {
    # ... existing moods ...
    "curious": "Inquisitive. Asks clarifying questions."
}
```
