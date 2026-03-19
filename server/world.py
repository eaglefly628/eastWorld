"""Game world: map, NPCs, and player management."""

from __future__ import annotations

import random
import string

from server.models import NPC, Player, Position


# 40x30 tile map — 0=sand, 1=road, 2=building, 3=water, 4=cactus, 5=rock
WORLD_MAP = [
    [0]*40 for _ in range(30)
]


def _init_map():
    """Lay out a small western town."""
    # Main road (horizontal)
    for x in range(40):
        WORLD_MAP[14][x] = 1
        WORLD_MAP[15][x] = 1
    # Cross road (vertical)
    for y in range(30):
        WORLD_MAP[y][20] = 1
        WORLD_MAP[y][21] = 1

    # Buildings
    buildings = [
        (3, 4, 7, 8),    # Sheriff's office
        (10, 4, 14, 8),   # Saloon
        (24, 4, 28, 8),   # General store
        (3, 18, 7, 22),   # Doctor's office
        (10, 18, 14, 22), # Bank
        (24, 18, 28, 22), # Stables
        (32, 4, 36, 8),   # Church
        (32, 18, 36, 22), # Hotel
    ]
    for x1, y1, x2, y2 in buildings:
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                WORLD_MAP[y][x] = 2

    # Water (small pond)
    for y in range(26, 29):
        for x in range(35, 39):
            WORLD_MAP[y][x] = 3

    # Scatter some cacti and rocks
    random.seed(42)
    for _ in range(15):
        x, y = random.randint(0, 39), random.randint(0, 29)
        if WORLD_MAP[y][x] == 0:
            WORLD_MAP[y][x] = 4
    for _ in range(10):
        x, y = random.randint(0, 39), random.randint(0, 29)
        if WORLD_MAP[y][x] == 0:
            WORLD_MAP[y][x] = 5


_init_map()


# ─── NPC Definitions (Western theme) ───────────────────────────────

NPCS: dict[str, NPC] = {}


def _create_npcs():
    npc_defs = [
        {
            "id": "sheriff",
            "name": "Sheriff Buck",
            "persona": (
                "You are Sheriff Buck, the tough but fair lawman of Dusty Gulch. "
                "You've kept this town safe for 15 years. You're suspicious of strangers "
                "but warm up once you trust someone. You have a secret: you once let an "
                "outlaw go because he saved your daughter's life."
            ),
            "position": Position(5, 10),
            "sprite": "sheriff",
            "greeting": "I'm the law around here. State your business.",
        },
        {
            "id": "saloon_keeper",
            "name": "Miss Ruby",
            "persona": (
                "You are Miss Ruby, owner of the Red Dust Saloon. You're charming, witty, "
                "and the biggest gossip in town. Everyone tells you their secrets over whiskey. "
                "You know where the old gold mine is but won't tell just anyone."
            ),
            "position": Position(12, 10),
            "sprite": "saloon",
            "greeting": "Welcome to the Red Dust! What's your poison, darlin'?",
        },
        {
            "id": "doctor",
            "name": "Doc Whitfield",
            "persona": (
                "You are Doc Whitfield, the town's only doctor. You came from back East, "
                "educated at Harvard. You're calm, intellectual, and slightly out of place "
                "in this rough town. You have a drinking problem you try to hide."
            ),
            "position": Position(5, 24),
            "sprite": "doctor",
            "greeting": "Good day. I hope you're here for a social call, not a medical one.",
        },
        {
            "id": "outlaw",
            "name": "Rattlesnake Pete",
            "persona": (
                "You are Rattlesnake Pete, a notorious outlaw hiding in plain sight. "
                "You pretend to be a simple drifter, but you're planning the biggest heist "
                "this territory has ever seen. You're charming but dangerous. "
                "You trust nobody, but you might let something slip to someone clever enough."
            ),
            "position": Position(26, 10),
            "sprite": "outlaw",
            "greeting": "*tips hat* Just a humble traveler, friend. Nothing more.",
        },
        {
            "id": "preacher",
            "name": "Father Cornelius",
            "persona": (
                "You are Father Cornelius, the town preacher. You're kind and patient, "
                "but you carry guilt about your past — you were once a gunslinger. "
                "You found God after a tragedy and now seek redemption through helping others."
            ),
            "position": Position(34, 10),
            "sprite": "preacher",
            "greeting": "Blessings upon you, child. All are welcome in God's house.",
        },
        {
            "id": "banker",
            "name": "Mr. Blackwood",
            "persona": (
                "You are Mr. Blackwood, the banker. You're shrewd, calculating, and "
                "obsessed with money and power. You secretly own half the town through "
                "various schemes. You speak politely but every word is measured."
            ),
            "position": Position(12, 24),
            "sprite": "banker",
            "greeting": "Good day. Time is money, so let's not waste either.",
        },
        {
            "id": "stable_hand",
            "name": "Young Billy",
            "persona": (
                "You are Young Billy, the 16-year-old stable hand. You're eager, naive, "
                "and dream of becoming a famous cowboy. You idolize Sheriff Buck and "
                "accidentally overhear things you shouldn't. You'll share rumors eagerly."
            ),
            "position": Position(26, 24),
            "sprite": "stable",
            "greeting": "Howdy mister! You got the finest horse I ever seen! ...Well, maybe.",
        },
        {
            "id": "hotel_owner",
            "name": "Madame Chen",
            "persona": (
                "You are Madame Chen, who runs the town hotel. You immigrated from China "
                "and built your business from nothing. You're wise, observant, and see "
                "everything that happens in town from your front desk. You speak with "
                "quiet authority and give cryptic but useful advice."
            ),
            "position": Position(34, 24),
            "sprite": "hotel",
            "greeting": "Welcome, traveler. You look like you've come a long way.",
        },
    ]

    for d in npc_defs:
        NPCS[d["id"]] = NPC(**d)


_create_npcs()


# ─── Player management ──────────────────────────────────────────────

PLAYERS: dict[str, Player] = {}
PLAYER_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e84393",
]
_color_index = 0


def add_player(player_id: str, name: str) -> Player:
    global _color_index
    player = Player(
        id=player_id,
        name=name,
        position=Position(20, 15),  # Spawn on the crossroads
        color=PLAYER_COLORS[_color_index % len(PLAYER_COLORS)],
    )
    PLAYERS[player_id] = player
    _color_index += 1
    return player


def remove_player(player_id: str):
    PLAYERS.pop(player_id, None)


def get_nearby_npc(player: Player, radius: float = 3.0) -> NPC | None:
    """Find the closest NPC within radius."""
    closest = None
    min_dist = radius
    for npc in NPCS.values():
        dist = player.position.distance_to(npc.position)
        if dist < min_dist:
            min_dist = dist
            closest = npc
    return closest


def get_world_state() -> dict:
    """Return full world state for client sync."""
    return {
        "map": WORLD_MAP,
        "npcs": [npc.to_dict() for npc in NPCS.values()],
        "players": [p.to_dict() for p in PLAYERS.values()],
        "map_width": 40,
        "map_height": 30,
    }
