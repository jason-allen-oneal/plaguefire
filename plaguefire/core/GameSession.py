from dataclasses import dataclass

from plaguefire.models.CharacterClass import get_character_class, list_character_classes
from plaguefire.models.Player import Player
from plaguefire.models.Race import get_race, list_races


@dataclass
class CommandResult:
    text: str
    should_quit: bool = False


class GameSession:
    def __init__(self, player: Player | None = None):
        self.player = player or Player()

    def handle_command(self, command: str) -> CommandResult:
        command = command.strip()

        if not command:
            return CommandResult("")

        normalized = command.lower()

        if normalized in {"quit", "exit"}:
            return CommandResult("The plaguefire fades.", should_quit=True)

        if normalized in {"help", "?"}:
            return CommandResult(self.help_text())

        if normalized in {"stats", "status"}:
            return CommandResult(self.stats())

        if normalized in {"spells", "spellbook"}:
            return CommandResult(self.spells())

        if normalized in {"races", "list races"}:
            return CommandResult(self.list_races_text())

        if normalized in {"classes", "list classes"}:
            return CommandResult(self.list_classes_text())

        if normalized.startswith("name "):
            return CommandResult(self.set_name(command[5:].strip()))

        if normalized.startswith("sex "):
            return CommandResult(self.set_sex(command[4:].strip()))

        if normalized.startswith("race "):
            return CommandResult(self.set_race(command[5:].strip()))

        if normalized.startswith("class "):
            return CommandResult(self.set_class(command[6:].strip()))

        if normalized.startswith("learn "):
            return CommandResult(self.learn_spell(command[6:].strip()))

        if normalized.startswith("damage "):
            return CommandResult(self.damage(command[7:].strip()))

        if normalized.startswith("heal "):
            return CommandResult(self.heal(command[5:].strip()))

        if normalized.startswith("xp "):
            return CommandResult(self.gain_xp(command[3:].strip()))

        if normalized.startswith("gold "):
            return CommandResult(self.gain_gold(command[5:].strip()))

        return CommandResult("Unknown command. Type help.")

    def help_text(self) -> str:
        return (
            "Commands:\n"
            "  help\n"
            "  name <name>\n"
            "  sex <sex>\n"
            "  races\n"
            "  race <race>\n"
            "  classes\n"
            "  class <class>\n"
            "  stats\n"
            "  spells\n"
            "  learn <spell>\n"
            "  damage <amount>\n"
            "  heal <amount>\n"
            "  xp <amount>\n"
            "  gold <amount>\n"
            "  quit"
        )

    def set_name(self, name: str) -> str:
        if not name:
            return "Name cannot be empty."

        self.player.name = name
        return f"Your name is now {self.player.name}."

    def set_sex(self, sex: str) -> str:
        if not sex:
            return "Sex cannot be empty."

        self.player.sex = sex
        return f"Sex set to {self.player.sex}."

    def set_race(self, race_name: str) -> str:
        try:
            race = get_race(race_name)
        except ValueError as error:
            return str(error)

        self.player.apply_race(race)
        return f"Race set to {self.player.race}."

    def set_class(self, class_name: str) -> str:
        try:
            character_class = get_character_class(class_name)
        except ValueError as error:
            return str(error)

        self.player.apply_character_class(character_class)
        return f"Class set to {self.player.character_class}."

    def list_races_text(self) -> str:
        lines = ["Available races:"]

        for race in list_races():
            lines.append(f"  - {race.name}: {race.description}")

        return "\n".join(lines)

    def list_classes_text(self) -> str:
        lines = ["Available classes:"]

        for character_class in list_character_classes():
            lines.append(f"  - {character_class.name}: {character_class.description}")

        return "\n".join(lines)

    def stats(self) -> str:
        player = self.player

        return (
            f"Name: {player.name or 'Unnamed'}\n"
            f"Age: {player.age}\n"
            f"Race: {player.race or 'Unknown'}\n"
            f"Class: {player.character_class or 'Unknown'}\n"
            f"Sex: {player.sex or 'Unknown'}\n"
            f"History: {player.history or 'Unknown'}\n"
            f"Social: {player.social or 'Unknown'}\n"
            f"Height: {player.height}\n"
            f"Weight: {player.weight}\n"
            f"Level: {player.level}\n"
            f"XP: {player.xp}/{player.next_level_xp}\n"
            f"Gold: {player.gold}\n"
            f"HP: {player.hp}/{player.max_hp}\n"
            f"Mana: {player.mana}/{player.max_mana}"
        )

    def spells(self) -> str:
        if not self.player.spells:
            return "You know no spells."

        return "Known spells:\n" + "\n".join(f"  - {spell}" for spell in self.player.spells)

    def learn_spell(self, spell_name: str) -> str:
        if self.player.learn_spell(spell_name):
            return f"You learned {spell_name}."

        return "You already know that spell, or the spell name was empty."

    def damage(self, amount_text: str) -> str:
        amount = self.parse_positive_int(amount_text)

        if amount is None:
            return "Damage amount must be a positive number."

        self.player.take_damage(amount)

        if not self.player.is_alive():
            return f"You take {amount} damage. You are dead."

        return f"You take {amount} damage. HP: {self.player.hp}/{self.player.max_hp}"

    def heal(self, amount_text: str) -> str:
        amount = self.parse_positive_int(amount_text)

        if amount is None:
            return "Heal amount must be a positive number."

        old_hp = self.player.hp
        self.player.heal(amount)

        return f"You heal {self.player.hp - old_hp} HP. HP: {self.player.hp}/{self.player.max_hp}"

    def gain_xp(self, amount_text: str) -> str:
        amount = self.parse_positive_int(amount_text)

        if amount is None:
            return "XP amount must be a positive number."

        old_level = self.player.level
        self.player.gain_xp(amount)

        if self.player.level > old_level:
            return f"You gain {amount} XP and reach level {self.player.level}."

        return f"You gain {amount} XP. XP: {self.player.xp}/{self.player.next_level_xp}"

    def gain_gold(self, amount_text: str) -> str:
        amount = self.parse_positive_int(amount_text)

        if amount is None:
            return "Gold amount must be a positive number."

        self.player.gain_gold(amount)

        return f"You gain {amount} gold. Gold: {self.player.gold}"

    @staticmethod
    def parse_positive_int(value: str) -> int | None:
        try:
            amount = int(value)
        except ValueError:
            return None

        if amount <= 0:
            return None

        return amount
