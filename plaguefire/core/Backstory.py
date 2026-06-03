from __future__ import annotations

import random
from typing import Any


BackstoryOption = dict[str, Any]
BackstoryTable = dict[str, Any]


BACKSTORY_TABLES: dict[str, BackstoryTable] = {
    "Human": {
        "templates": [
            {
                "pattern": "You {origin}, {upbringing}. {mentor} {turning} {calling}",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 50,
                "base_gold": 100,
            },
            {
                "pattern": "You {origin}. {turning} {upbringing} {calling}",
                "slots": ["origin", "turning", "upbringing", "calling"],
                "base_social": 48,
                "base_gold": 95,
            },
        ],
        "origin": [
            {"text": "were born in Greyharbor's Riverside, among fish smoke, tar, and shouting dockhands", "social": -3, "gold": -10},
            {"text": "came from Dalehaven grain country, where the Rupture left weak soil and hard people", "social": 0, "gold": 0},
            {"text": "were raised near a ruined border keep on the old trade roads", "social": -4, "gold": -15},
            {"text": "grew up under a merchant roof in Delinor, close enough to wealth to smell it and far enough to starve", "social": 8, "gold": 25},
            {"text": "were born in the Outmarsh, where names are traded, stolen, and forgotten", "social": -12, "gold": -30},
        ],
        "upbringing": [
            {"text": "you learned discipline from hunger and caution from debt", "social": -2, "gold": -5},
            {"text": "your family survived by moving goods nobody wanted listed in a ledger", "social": 2, "gold": 20},
            {"text": "you were taught to keep your head down when the Iron Guard passed", "social": -5, "gold": -5},
            {"text": "you learned letters from a failed clerk who drank away better days", "social": 5, "gold": 5},
            {"text": "you grew up around refugees who still counted years from the Rupture", "social": -6, "gold": -10},
        ],
        "mentor": [
            {"text": "A river smuggler taught you which smiles meant knives.", "social": 2, "gold": 15},
            {"text": "A dismissed Iron Guard veteran taught you how order rots from inside armor.", "social": 4, "gold": 10},
            {"text": "A Veyrian exile taught you old histories no one in Greyharbor cared to remember.", "social": 5, "gold": 0},
            {"text": "A street priest of Selmira taught you mercy, then vanished during a plaguefire scare.", "social": 0, "gold": -5},
            {"text": "No one taught you anything gently.", "social": -6, "gold": -10},
        ],
        "turning": [
            {"text": "When plaguefire relics surfaced near your home, everything familiar became dangerous.", "social": -4, "gold": 20},
            {"text": "When a noble house bought your family's silence, you learned what law was worth.", "social": 3, "gold": 30},
            {"text": "When mutant things came up from the marsh, you were one of the few who ran the right way.", "social": -2, "gold": 0},
            {"text": "When the caravans started moving again, you followed the coin toward Greyharbor.", "social": 2, "gold": 20},
            {"text": "When you were accused of witch-work, leaving became survival.", "social": -10, "gold": -20},
        ],
        "calling": [
            {"text": "Now you descend for coin, proof, and a way out.", "social": 0, "gold": 10},
            {"text": "Now you seek the old fire because every safer road is already owned.", "social": -2, "gold": 0},
            {"text": "Now you hunt relics for buyers who pretend not to know your name.", "social": 3, "gold": 25},
            {"text": "Now you carry old anger into the dark.", "social": -1, "gold": 0},
        ],
    },
    "Half-Elf": {
        "templates": [
            {
                "pattern": "You {origin}, {upbringing}. {mentor} {turning} {calling}",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 45,
                "base_gold": 100,
            }
        ],
        "origin": [
            {"text": "were born between Greyharbor blood and elven exile, accepted by neither side for long", "social": -8, "gold": -10},
            {"text": "grew up near the Outmarsh edge, where human fear and elven silence met in the same mud", "social": -12, "gold": -20},
            {"text": "were raised in Olthryan dockyards among traders who valued your ears less than your usefulness", "social": -4, "gold": 10},
            {"text": "came from a hidden forest refuge that sent you away before human suspicion found it", "social": 0, "gold": 0},
        ],
        "upbringing": [
            {"text": "you learned to hear insults before blades followed them", "social": -3, "gold": 0},
            {"text": "you passed messages between people who would not be seen speaking together", "social": 4, "gold": 20},
            {"text": "you were taught old songs no human wanted sung after the Rupture", "social": 2, "gold": 0},
            {"text": "you learned that being useful was safer than being welcome", "social": -2, "gold": 10},
        ],
        "mentor": [
            {"text": "A Thalyrian archivist taught you to read forbidden marginalia.", "social": 8, "gold": 10},
            {"text": "A Ha'alazi relic trader taught you that beautiful things can hate being touched.", "social": 4, "gold": 25},
            {"text": "An elven scout taught you patience, then left without farewell.", "social": 0, "gold": 0},
            {"text": "A Syndicate runner taught you which doors only look locked.", "social": -2, "gold": 20},
        ],
        "turning": [
            {"text": "When an Outmarsh mob blamed you for green fire in the reeds, you learned how quickly fear chooses a face.", "social": -15, "gold": -20},
            {"text": "When the Iron Guard raided your street, your mixed blood saved you from one accusation and earned you three more.", "social": -10, "gold": -10},
            {"text": "When a Vaelith cult mistook your dreams for prophecy, you ran before they could make you holy.", "social": -12, "gold": 5},
            {"text": "When a noble paid for your silence, you discovered silence has a market rate.", "social": 5, "gold": 35},
        ],
        "calling": [
            {"text": "Now you enter the dark because the surface never made room for you.", "social": -2, "gold": 0},
            {"text": "Now you seek relics, leverage, and a name no one can take back.", "social": 3, "gold": 15},
            {"text": "Now you follow the old fire, though part of you knows it has already noticed.", "social": -4, "gold": 5},
        ],
    },
    "Elf": {
        "templates": [
            {
                "pattern": "You {origin}. {upbringing} {turning} {calling}",
                "slots": ["origin", "upbringing", "turning", "calling"],
                "base_social": 55,
                "base_gold": 110,
            }
        ],
        "origin": [
            {"text": "came from a forest sanctuary that survived the Rupture with its magic intact", "social": 5, "gold": 10},
            {"text": "were sent from an old grove to watch human cities rebuild badly", "social": 8, "gold": 15},
            {"text": "were born among refugees who hated elven magic almost as much as they needed it", "social": -8, "gold": -10},
        ],
        "upbringing": [
            {"text": "You were taught that nature remembers what stone forgets.", "social": 2, "gold": 0},
            {"text": "You learned healing arts from elders who refused to call them spells.", "social": 4, "gold": 5},
            {"text": "You learned to hide your gifts in human streets.", "social": -4, "gold": 0},
        ],
        "turning": [
            {"text": "When Greyharbor merchants tried to buy what your people would not sell, you left with their map and not their permission.", "social": -2, "gold": 30},
            {"text": "When a grove elder named the Plaguefire an old wound, you were sent to look into it.", "social": 5, "gold": 10},
            {"text": "When frightened humans called your magic Rupture-work, patience stopped being enough.", "social": -10, "gold": -5},
        ],
        "calling": [
            {"text": "Now you descend to learn whether the old fire can be healed or only buried deeper.", "social": 0, "gold": 5},
            {"text": "Now you seek proof that the world broke from greed, not magic itself.", "social": 3, "gold": 10},
        ],
    },
    "Halfling": {
        "templates": [
            {
                "pattern": "You {origin}, {upbringing}. {turning} {calling}",
                "slots": ["origin", "upbringing", "turning", "calling"],
                "base_social": 48,
                "base_gold": 90,
            }
        ],
        "origin": [
            {"text": "were born in Dalehaven river country, where food is politics and harvests are never certain", "social": 0, "gold": 0},
            {"text": "grew up on a grain barge bound for Greyharbor markets", "social": 2, "gold": 15},
            {"text": "came from a farmstead half-ruined by mutated pests and failing soil", "social": -6, "gold": -15},
        ],
        "upbringing": [
            {"text": "you learned ledgers, knots, and how to smile at armed taxmen", "social": 5, "gold": 15},
            {"text": "you learned that being underestimated is a weapon", "social": 0, "gold": 5},
            {"text": "you grew up feeding people who would later try to cheat you", "social": 2, "gold": -5},
        ],
        "turning": [
            {"text": "When Greyharbor buyers squeezed your family dry, you followed the money back to its source.", "social": -3, "gold": 10},
            {"text": "When something plague-touched got into the grain stores, you survived by being quicker than panic.", "social": -4, "gold": -5},
            {"text": "When river trade resumed, you found more danger in opportunity than in famine.", "social": 4, "gold": 25},
        ],
        "calling": [
            {"text": "Now you go below because small hands can carry heavy fortunes.", "social": 0, "gold": 10},
            {"text": "Now you seek enough coin to make every merchant remember your name.", "social": 4, "gold": 20},
        ],
    },
    "Gnome": {
        "templates": [
            {
                "pattern": "You {origin}. {upbringing} {mentor} {turning} {calling}",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 45,
                "base_gold": 95,
            }
        ],
        "origin": [
            {"text": "were born in an Olthryan guild quarter full of gears, dyes, smoke, and bad ideas", "social": 5, "gold": 10},
            {"text": "grew up in a hidden Greyharbor workshop that repaired relics no one admitted owning", "social": -2, "gold": 25},
            {"text": "came from a family of alchemists whose neighbors kept buckets of sand by every door", "social": -5, "gold": 5},
        ],
        "upbringing": [
            {"text": "You learned that if a device screams, it is not always broken.", "social": -1, "gold": 10},
            {"text": "You learned locks, powders, lenses, and the value of a quick exit.", "social": 2, "gold": 20},
            {"text": "You learned to replace lost magic with mechanisms that only sometimes exploded.", "social": 0, "gold": 15},
        ],
        "mentor": [
            {"text": "A guild artificer taught you precision and blamed you for every blast mark.", "social": 5, "gold": 15},
            {"text": "A black-market appraiser taught you how to spot true Plaguefire glass.", "social": -2, "gold": 30},
            {"text": "A half-mad tinkerer taught you that impossible is usually just expensive.", "social": -4, "gold": 5},
        ],
        "turning": [
            {"text": "When your experiment woke something inside a relic, your workshop stopped being a safe place.", "social": -10, "gold": -10},
            {"text": "When a noble house stole your design, you decided ruins were more honest than patrons.", "social": -3, "gold": 5},
            {"text": "When the guild banned your work, private buyers became your only teachers.", "social": -8, "gold": 20},
        ],
        "calling": [
            {"text": "Now you descend to test theories no sane academy would fund.", "social": -2, "gold": 10},
            {"text": "Now you hunt relics because broken things make the best teachers.", "social": 0, "gold": 20},
        ],
    },
    "Dwarf": {
        "templates": [
            {
                "pattern": "You {origin}. {upbringing} {turning} {calling}",
                "slots": ["origin", "upbringing", "turning", "calling"],
                "base_social": 52,
                "base_gold": 115,
            }
        ],
        "origin": [
            {"text": "were born under stone, where the Throne of the Gods is not metaphor but mountain", "social": 5, "gold": 15},
            {"text": "came from Riven's fortified riverworks, where dwarven craft holds human walls together", "social": 6, "gold": 20},
            {"text": "were raised among ore caravans that every kingdom wanted taxed, guarded, or stolen", "social": 2, "gold": 25},
        ],
        "upbringing": [
            {"text": "You learned that a debt can outlive a king.", "social": 2, "gold": 5},
            {"text": "You learned stonecraft, oathcraft, and the proper weight of grudges.", "social": 4, "gold": 10},
            {"text": "You learned to distrust anything built by wizardry instead of hands.", "social": 0, "gold": 0},
        ],
        "turning": [
            {"text": "When a tunnel glassed over from old leyfire, you saw what human magic had done below the roots of mountains.", "social": -2, "gold": 5},
            {"text": "When Riven's lords bent too low to Greyharbor coin, you took your oath elsewhere.", "social": -4, "gold": 10},
            {"text": "When a family relic was sold into Delinor, you followed it toward the coast.", "social": 0, "gold": 25},
        ],
        "calling": [
            {"text": "Now you descend because old wounds are best judged underground.", "social": 0, "gold": 10},
            {"text": "Now you seek ore, honor, and proof that some fires should be sealed forever.", "social": 3, "gold": 20},
        ],
    },
    "Half-Orc": {
        "templates": [
            {
                "pattern": "You {origin}, {upbringing}. {turning} {calling}",
                "slots": ["origin", "upbringing", "turning", "calling"],
                "base_social": 30,
                "base_gold": 70,
            }
        ],
        "origin": [
            {"text": "were born in the borderlands between Dalehaven and Riven, where every map is an argument", "social": -6, "gold": -5},
            {"text": "grew up around mercenaries who respected strength more than names", "social": -2, "gold": 10},
            {"text": "were raised in Greyharbor alleys where people crossed the street before learning your voice", "social": -12, "gold": -15},
        ],
        "upbringing": [
            {"text": "you learned early that mercy is easier to show after winning", "social": -3, "gold": 0},
            {"text": "you learned to turn suspicion into silence", "social": -4, "gold": 0},
            {"text": "you found work where fear counted as a recommendation", "social": -2, "gold": 20},
        ],
        "turning": [
            {"text": "When an Iron Guard patrol needed someone to blame, your face was enough.", "social": -15, "gold": -10},
            {"text": "When a warband called you kin only after needing your blade, you left them with fewer blades.", "social": -8, "gold": 10},
            {"text": "When plague-touched raiders burned your road camp, survival became your only inheritance.", "social": -10, "gold": -5},
        ],
        "calling": [
            {"text": "Now you descend because monsters below are at least honest.", "social": -2, "gold": 5},
            {"text": "Now you seek coin heavy enough to change how people say your name.", "social": 0, "gold": 15},
        ],
    },
    "Half-Troll": {
        "templates": [
            {
                "pattern": "You {origin}. {upbringing} {turning} {calling}",
                "slots": ["origin", "upbringing", "turning", "calling"],
                "base_social": 20,
                "base_gold": 50,
            }
        ],
        "origin": [
            {"text": "were born where marsh water glowed wrong and people prayed you would not live long", "social": -15, "gold": -20},
            {"text": "came from the river ruins, feared before you were old enough to understand fear", "social": -18, "gold": -15},
            {"text": "were raised outside Greyharbor walls because inside them you were called a riot waiting to happen", "social": -20, "gold": -25},
        ],
        "upbringing": [
            {"text": "You learned to speak softly because your size did the shouting.", "social": -4, "gold": 0},
            {"text": "You learned that hunger, anger, and kindness all frighten small people when they come from you.", "social": -6, "gold": -5},
            {"text": "You survived by doing work nobody else could do and everybody else wanted forgotten.", "social": -5, "gold": 20},
        ],
        "turning": [
            {"text": "When a cult called your blood a blessing, you saw what worship does to monsters.", "social": -12, "gold": 5},
            {"text": "When the Iron Guard tried chains, you learned what chains cost.", "social": -18, "gold": -10},
            {"text": "When a child thanked you instead of screaming, you started walking before hope became dangerous.", "social": -4, "gold": 0},
        ],
        "calling": [
            {"text": "Now you descend because the dark does not flinch.", "social": -2, "gold": 0},
            {"text": "Now you hunt the old fire to learn whether you were made or merely blamed.", "social": -5, "gold": 10},
        ],
    },
}


def generate_backstory(race_name: str, rng: random.Random) -> dict[str, Any]:
    table = BACKSTORY_TABLES.get(race_name) or BACKSTORY_TABLES["Human"]
    return generate_backstory_entry(table, rng)


def generate_backstory_entry(table: BackstoryTable, rng: random.Random) -> dict[str, Any]:
    templates = table.get("templates", [])

    if not templates:
        return {
            "text": "Your early days are unrecorded.",
            "social": 50,
            "gold": 100,
        }

    template = dict(rng.choice(templates))
    slots = list(template.get("slots", []))

    values: dict[str, str] = {}
    social = int(template.get("base_social", 50))
    gold = int(template.get("base_gold", 100))

    for slot in slots:
        options = table.get(slot, [])

        if not options:
            values[slot] = slot
            continue

        choice = dict(rng.choice(options))
        values[slot] = str(choice.get("text", ""))
        social += int(choice.get("social", 0))
        gold += int(choice.get("gold", 0))

    pattern = str(template.get("pattern", "Your early days are unrecorded."))

    try:
        text = pattern.format(**values)
    except KeyError:
        text = pattern

    return {
        "text": normalize_backstory_text(text),
        "social": max(1, min(100, social)),
        "gold": max(20, gold),
    }


def normalize_backstory_text(text: str) -> str:
    text = " ".join(text.split())

    if text and text[-1] not in ".!?":
        text += "."

    return text
