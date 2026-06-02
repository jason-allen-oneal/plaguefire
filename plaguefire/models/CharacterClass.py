from dataclasses import dataclass, field


@dataclass(frozen=True)
class CharacterClass:
    name: str
    description: str = ""

    max_hp_bonus: int = 0
    max_mana_bonus: int = 0

    starting_gold: int = 0
    starting_spells: list[str] = field(default_factory=list)


CHARACTER_CLASSES: dict[str, CharacterClass] = {
    "warrior": CharacterClass(
        name="Warrior",
        description="A hardened fighter built for direct violence.",
        max_hp_bonus=8,
        max_mana_bonus=0,
        starting_gold=15,
    ),
    "pyromancer": CharacterClass(
        name="Pyromancer",
        description="A dangerous caster trained to shape plaguefire without being consumed by it.",
        max_hp_bonus=2,
        max_mana_bonus=8,
        starting_gold=8,
        starting_spells=["Ember"],
    ),
    "gravebound": CharacterClass(
        name="Gravebound",
        description="A grim wanderer who learned survival from tombs, ruins, and bad omens.",
        max_hp_bonus=5,
        max_mana_bonus=3,
        starting_gold=5,
        starting_spells=["Bone Whisper"],
    ),
}


def get_character_class(name: str) -> CharacterClass:
    key = name.strip().lower()

    if key not in CHARACTER_CLASSES:
        valid = ", ".join(sorted(character_class.name for character_class in CHARACTER_CLASSES.values()))
        raise ValueError(f"Unknown class '{name}'. Valid classes: {valid}")

    return CHARACTER_CLASSES[key]


def list_character_classes() -> list[CharacterClass]:
    return list(CHARACTER_CLASSES.values())
