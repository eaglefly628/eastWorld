"""Data models for EastWorld."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class Position:
    x: int
    y: int

    def distance_to(self, other: Position) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class Memory:
    """A single memory entry for an NPC."""
    player_name: str
    content: str
    timestamp: float = field(default_factory=time.time)
    importance: int = 5  # 1-10 scale

    def to_dict(self) -> dict:
        return {
            "player_name": self.player_name,
            "content": self.content,
            "timestamp": self.timestamp,
            "importance": self.importance,
        }


@dataclass
class NPC:
    """An NPC agent in the world."""
    id: str
    name: str
    persona: str  # Character backstory and personality
    position: Position
    sprite: str  # Emoji or sprite identifier
    memories: list[Memory] = field(default_factory=list)
    greeting: str = "Howdy, stranger."

    def add_memory(self, player_name: str, content: str, importance: int = 5):
        self.memories.append(Memory(
            player_name=player_name,
            content=content,
            importance=importance,
        ))
        # Keep last 100 memories per NPC
        if len(self.memories) > 100:
            self.memories = sorted(
                self.memories, key=lambda m: m.importance, reverse=True
            )[:80]

    def get_relevant_memories(self, player_name: str | None = None, limit: int = 10) -> list[Memory]:
        memories = self.memories
        if player_name:
            # Prioritize memories about this player, but include others too
            player_memories = [m for m in memories if m.player_name == player_name]
            other_memories = [m for m in memories if m.player_name != player_name]
            memories = player_memories + other_memories
        return memories[-limit:]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "position": {"x": self.position.x, "y": self.position.y},
            "sprite": self.sprite,
            "greeting": self.greeting,
        }


@dataclass
class Player:
    """A connected player."""
    id: str
    name: str
    position: Position
    color: str = "#e74c3c"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "position": {"x": self.position.x, "y": self.position.y},
            "color": self.color,
        }
