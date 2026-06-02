from dataclasses import dataclass, field


@dataclass(frozen=True)
class Race:
    name: str
    description: str = ""

    age: int = 18
    height: int = 170
    weight: int = 70

    history: str = ""
    social: str = ""

    max_hp_bonus: int = 0
    max_mana_bonus: int = 0

    starting_spells: list[str] = field(default_factory=list)


RACES: dict[str, Race] = {
    "human": Race(
        name="Human",
        description="Adaptable survivors with no extreme strengths or weaknesses.",
        age=24,
        height=175,
        weight=78,
        history="You were born beyond the ash roads, where old kingdoms still pretend they are alive.",
        social="Humans are common enough to pass unnoticed in most settlements.",
        max_hp_bonus=2,
        max_mana_bonus=1,
    ),
    "ashborn": Race(
        name="Ashborn",
        description="A people marked by plaguefire exposure and stubborn survival.",
        age=31,
        height=168,
        weight=66,
        history="You were raised under falling ash and learned early that clean air is a luxury.",
        social="Ashborn are treated with suspicion, fear, and occasional reverence.",
        max_hp_bonus=1,
        max_mana_bonus=3,
        starting_spells=["Cinder Touch"],
    ),
    "hollowkin": Race(
        name="Hollowkin",
        description="Gaunt survivors touched by death but not claimed by it.",
        age=42,
        height=182,
        weight=61,
        history="You remember dying. You do not remember staying dead.",
        social="Most people avoid Hollowkin unless desperation forces conversation.",
        max_hp_bonus=4,
        max_mana_bonus=0,
    ),
}


def get_race(name: str) -> Race:
    key = name.strip().lower()

    if key not in RACES:
        valid = ", ".join(sorted(race.name for race in RACES.values()))
        raise ValueError(f"Unknown race '{name}'. Valid races: {valid}")

    return RACES[key]


def list_races() -> list[Race]:
    return list(RACES.values())
