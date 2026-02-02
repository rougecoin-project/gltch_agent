# Concepts

Understanding the GLTCH architecture and design.

## Topics

- [Architecture](architecture.md) - System components and how they connect
- [Agent](agent.md) - The Python agent core
- [Gateway](gateway.md) - The TypeScript WebSocket hub
- [Personality](personality.md) - Modes, moods, and emotions
- [Gamification](gamification.md) - XP, ranks, and unlocks
- [Tools](tools.md) - Action tags and tool execution

## Overview

GLTCH is a multi-component system:

```
┌─────────────────────────────────────────────────────────┐
│                        Channels                          │
│   Discord    │    Telegram    │    WebChat              │
└──────────────┴────────────────┴─────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                        Gateway                           │
│   HTTP Server  │  WebSocket Hub  │  Message Router      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼  JSON-RPC
┌─────────────────────────────────────────────────────────┐
│                         Agent                            │
│   LLM Engine  │  Memory  │  Tools  │  Personality       │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Local-First

GLTCH runs entirely on your machine by default. The LLM runs via Ollama, and all data stays local.

### 2. Modular

Each component (agent, gateway, channels) is independent and can be replaced or extended.

### 3. Personality-Driven

GLTCH isn't just an assistant - she has personality, moods, and attitude. This makes interactions more engaging.

### 4. Gamified

XP, levels, and unlocks reward continued use and make progression visible.

### 5. Secure by Default

Network access is disabled by default. Tool execution requires confirmation.
