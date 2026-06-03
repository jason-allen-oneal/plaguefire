import random

from plaguefire.core.CharacterCreation import create_player_data, generate_history


def test_old_style_backstory_generation_is_structured_and_deterministic():
    first = generate_history("Half-Elf", random.Random(42))
    second = generate_history("Half-Elf", random.Random(42))

    assert first == second
    assert len(first["text"]) > 120
    assert isinstance(first["social"], int)
    assert isinstance(first["gold"], int)
    assert 1 <= first["social"] <= 100
    assert first["gold"] >= 20


def test_backstory_generation_uses_world_lore():
    histories = [
        generate_history("Human", random.Random(seed))["text"]
        for seed in range(20)
    ]

    joined = " ".join(histories)

    assert any(
        term in joined
        for term in [
            "Greyharbor",
            "Outmarsh",
            "Rupture",
            "Iron Guard",
            "plaguefire",
            "Dalehaven",
        ]
    )


def test_half_elf_backstories_include_outcast_or_greyharbor_flavor():
    histories = [
        generate_history("Half-Elf", random.Random(seed))["text"]
        for seed in range(20)
    ]

    joined = " ".join(histories)

    assert any(
        term in joined
        for term in [
            "Outmarsh",
            "Iron Guard",
            "Vaelith",
            "Greyharbor",
            "elven",
            "Syndicate",
        ]
    )


def test_create_player_data_stores_structured_backstory_social_and_gold():
    data = create_player_data(
        name="Rev",
        race_name="Human",
        class_name="Warrior",
        sex="Male",
        seed=123,
    )

    assert len(data["history"]) > 120
    assert isinstance(data["social"], int)
    assert data["gold"] >= 20
    assert any(
        term in data["history"]
        for term in [
            "Greyharbor",
            "Outmarsh",
            "Rupture",
            "Iron Guard",
            "Dalehaven",
            "plaguefire",
        ]
    )
