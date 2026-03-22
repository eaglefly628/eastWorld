"""NPC AI Agent system with pluggable backends (mock / Claude API)."""

from __future__ import annotations

import os
import random
from abc import ABC, abstractmethod

from server.models import NPC, Memory


class AgentBackend(ABC):
    """Base class for NPC response generation."""

    @abstractmethod
    async def generate_response(
        self, npc: NPC, player_name: str, message: str
    ) -> str:
        ...


class MockBackend(AgentBackend):
    """Mock backend that generates contextual responses without an LLM."""

    TEMPLATES = {
        "greeting": [
            "Well, well... {player_name}. What brings you to these parts?",
            "Ah, {player_name}! I was just thinking about you.",
            "{player_name}, good to see a friendly face around here.",
            "You again, {player_name}? Heh, I don't mind the company.",
        ],
        "has_memory": [
            "I remember you told me about {topic}. What's new?",
            "Last time we spoke, you mentioned {topic}. Still on your mind?",
            "Ah yes, {topic}... I've been thinking about that since you mentioned it.",
        ],
        "default": [
            "Interesting... tell me more about that, {player_name}.",
            "Hmm, that's something to think about. Life out here ain't simple.",
            "You don't say! Things sure are changing in these parts.",
            "I've heard stranger things, but not by much, {player_name}.",
            "Well now, that's a tale worth remembering.",
            "The desert wind carries many stories... yours is one of 'em.",
            "Reckon that's the kind of thing that keeps a man up at night.",
        ],
        "farewell": [
            "Safe travels, {player_name}. Watch your back out there.",
            "Come back anytime, {player_name}. Door's always open.",
            "Until next time. The west is a dangerous place to be alone.",
        ],
    }

    CAT_RESPONSES = {
        "age": [
            "*stretches lazily* Meow~ I'm 5 years old! That's like... a lot in cat years.",
            "*yawns* 5 years old, obviously. Now scratch my chin.",
            "I'm 5! My owner CC says I don't look a day over 3. *purrs proudly*",
        ],
        "owner": [
            "*purrs* CC is my human! They give me the best treats~",
            "My owner CC? The best human ever. Junbai's first cat, that's me! *tail swish*",
            "CC takes care of me! I'm Junbai's first cat, you know. Very important. *licks paw*",
        ],
        "greeting": [
            "*rubs against your leg* Mrrrow~ Hello, {player_name}!",
            "*looks up with big eyes* Oh, a new friend! Meow~",
            "*flicks tail* You smell interesting, {player_name}. Pet me?",
        ],
        "default": [
            "*knocks something off a nearby table* Meow. What were you saying?",
            "*rolls over showing belly* ...It's a trap though. Don't touch.",
            "*chases own tail briefly* Sorry, what? I got distracted.",
            "*purrs loudly* Mrrrrrow~",
            "*stares at you intensely, then slowly blinks* That means I like you.",
            "*suddenly runs across the room for no reason* ZOOM! ...Okay I'm back.",
            "*sits in a sunbeam* Life is good, {player_name}. Life is good.",
        ],
        "farewell": [
            "*curls up into a ball* Bye bye~ Come back with treats!",
            "*slow blink* See you later, {player_name}. Meow~",
        ],
    }

    async def generate_response(
        self, npc: NPC, player_name: str, message: str
    ) -> str:
        msg_lower = message.lower()

        # Special handling for Lulu the cat
        if npc.id == "cat_lulu":
            return self._cat_response(npc, player_name, msg_lower)

        # Check for farewell
        if any(w in msg_lower for w in ["bye", "farewell", "see you", "leaving", "gotta go"]):
            template = random.choice(self.TEMPLATES["farewell"])
            return template.format(player_name=player_name)

        # Check for greeting
        if any(w in msg_lower for w in ["hello", "hi", "hey", "howdy", "greetings"]):
            recent = npc.get_relevant_memories(player_name, limit=3)
            if recent:
                template = random.choice(self.TEMPLATES["has_memory"])
                topic = recent[-1].content[:50]
                return template.format(player_name=player_name, topic=topic)
            template = random.choice(self.TEMPLATES["greeting"])
            return template.format(player_name=player_name)

        # Default: contextual response with persona flavor
        persona_hint = ""
        if "sheriff" in npc.persona.lower():
            persona_hint = "The law is the law. "
        elif "bartender" in npc.persona.lower() or "saloon" in npc.persona.lower():
            persona_hint = "*polishes a glass* "
        elif "doctor" in npc.persona.lower():
            persona_hint = "*adjusts spectacles* "
        elif "outlaw" in npc.persona.lower() or "bandit" in npc.persona.lower():
            persona_hint = "*leans against the wall* "

        template = random.choice(self.TEMPLATES["default"])
        response = persona_hint + template.format(player_name=player_name)

        # Record this interaction as a memory
        npc.add_memory(player_name, message, importance=5)

        return response

    def _cat_response(self, npc: NPC, player_name: str, msg_lower: str) -> str:
        """Generate Lulu the cat's responses."""
        # Age questions
        if any(w in msg_lower for w in [
            "old", "age", "多大", "几岁", "年龄", "year",
        ]):
            resp = random.choice(self.CAT_RESPONSES["age"])
            npc.add_memory(player_name, f"asked my age", importance=3)
            return resp.format(player_name=player_name)

        # Owner questions
        if any(w in msg_lower for w in [
            "owner", "cc", "junbai", "主人", "谁的猫",
        ]):
            resp = random.choice(self.CAT_RESPONSES["owner"])
            npc.add_memory(player_name, f"asked about my owner", importance=3)
            return resp.format(player_name=player_name)

        # Farewell
        if any(w in msg_lower for w in ["bye", "farewell", "see you", "再见", "走了"]):
            return random.choice(self.CAT_RESPONSES["farewell"]).format(player_name=player_name)

        # Greeting
        if any(w in msg_lower for w in ["hello", "hi", "hey", "howdy", "你好", "嗨"]):
            return random.choice(self.CAT_RESPONSES["greeting"]).format(player_name=player_name)

        # Default cat behavior
        npc.add_memory(player_name, msg_lower[:50], importance=3)
        return random.choice(self.CAT_RESPONSES["default"]).format(player_name=player_name)


class ClaudeBackend(AgentBackend):
    """Claude API backend for rich NPC responses."""

    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY", "")
            )
        except ImportError:
            raise RuntimeError("anthropic package required for Claude backend")

    async def generate_response(
        self, npc: NPC, player_name: str, message: str
    ) -> str:
        memories = npc.get_relevant_memories(player_name, limit=15)
        memory_text = "\n".join(
            f"- [{m.player_name}] said: {m.content}" for m in memories
        ) if memories else "No previous interactions."

        system_prompt = f"""You are {npc.name}, an NPC in a Western-themed open world game called EastWorld.

YOUR PERSONA:
{npc.persona}

YOUR MEMORIES OF PAST INTERACTIONS:
{memory_text}

RULES:
- Stay in character at all times
- Remember details from past conversations
- Be concise (1-3 sentences typically)
- React naturally to what players tell you
- You can have opinions, emotions, and secrets
- Never break the fourth wall
- Reference your memories when relevant"""

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"[{player_name} says to you]: {message}"}
            ],
        )

        reply = response.content[0].text

        # Record interaction in memory
        npc.add_memory(player_name, message, importance=5)

        return reply


def create_backend(backend_type: str = "mock") -> AgentBackend:
    """Factory function to create the appropriate backend."""
    if backend_type == "claude":
        return ClaudeBackend()
    return MockBackend()
