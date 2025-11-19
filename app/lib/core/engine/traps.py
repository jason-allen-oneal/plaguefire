import random
from typing import Any, Dict, List, Optional, Tuple

from app.lib.utils import _apply_damage_modifiers, _parse_damage_expr
from app.model.entity import Entity
from config import DOOR_OPEN, FLOOR, STAIRS_DOWN, STAIRS_UP


class TrapAndChestManager:
    def __init__(self, game):
        self.game = game
        # Traps & chests (position keyed)
        self.traps: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.chests: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.known_traps: set[Tuple[int, int]] = set()
        self._prev_player_pos: Optional[Tuple[int, int]] = None
    
    # =============================
    # Traps & Chests Implementation
    # =============================
    def _initialize_traps_and_chests(self) -> None:
        """Populate traps and chests on a newly generated dungeon level (depth>0)."""
        if self.game.current_depth <= 0 or not self.game.current_map:
            self.traps.clear()
            self.chests.clear()
            return
        
        
        trap_defs = getattr(self.game.loader, 'traps', {})
        chest_defs = getattr(self.game.loader, 'chests', {})
        base_trap_chance = 0.01 + min(0.04, self.game.current_depth * 0.0005)
        for y in range(1, self.game.map_height - 1):
            for x in range(1, self.game.map_width - 1):
                if self.game.current_map[y][x] != FLOOR:
                    continue
                if random.random() < base_trap_chance and trap_defs:
                    tdef = random.choice(list(trap_defs.values()))
                    self.traps[(x, y)] = {
                        'id': tdef['id'],
                        'data': tdef,
                        'revealed': False,
                        'disarmed': False,
                        'single_use': tdef.get('single_use', True)
                    }
        for room in self.game.rooms:
            if random.random() < 0.3 and chest_defs:
                cx, cy = room.center()
                if (0 <= cx < self.game.map_width and 0 <= cy < self.game.map_height and
                        self.game.current_map[cy][cx] == FLOOR and (cx, cy) not in self.traps and (cx, cy) not in self.chests):
                    cdef = random.choice(list(chest_defs.values()))
                    self.chests[(cx, cy)] = {
                        'id': cdef['id'],
                        'data': cdef,
                        'opened': False,
                        'revealed': False,
                        'disarmed': False,
                        'contents': self._generate_chest_loot(cdef)
                    }

    def _generate_chest_loot(self, cdef: Dict[str, Any]) -> List[str]:
        loot = []
        table = cdef.get('loot_table', [])
        max_loot = cdef.get('max_loot', 2)
        for entry in table:
            if len(loot) >= max_loot:
                break
            if not isinstance(entry, list) or len(entry) < 2:
                continue
            item_id, weight = entry[0], entry[1]
            if random.randint(1, 100) <= weight:
                loot.append(item_id)
        return loot

    def _attempt_detect_traps(self) -> None:
        if not self.game.player or not hasattr(self.game.player, 'position'):
            return
        px, py = self.game.player.position
        abilities = getattr(self.game.player, 'abilities', {})
        searching_skill = abilities.get('searching', 5)
        perception_skill = abilities.get('perception', 5)
        base_skill = (searching_skill + perception_skill) / 2.0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                tx, ty = px + dx, py + dy
                trap = self.traps.get((tx, ty))
                chest = self.chests.get((tx, ty))
                if trap and not trap['revealed']:
                    diff = trap['data'].get('detection_difficulty', 50)
                    chance = max(5.0, min(95.0, 15 + base_skill * 6 + getattr(self.game.player, 'level', 1) - diff))
                    if random.uniform(0, 100) <= chance:
                        trap['revealed'] = True
                        self.known_traps.add((tx, ty))
                        self.game.log_event('You spot a trap!')
                        try:
                            self.game.mark_dirty_tile(tx, ty)
                        except Exception:
                            pass
                if chest and not chest['revealed']:
                    diff = chest['data'].get('detection_difficulty', 40)
                    chance = max(5.0, min(95.0, 10 + base_skill * 5 + getattr(self.game.player, 'level', 1) - diff))
                    if random.uniform(0, 100) <= chance:
                        chest['revealed'] = True
                        self.game.log_event('You sense a chest nearby.')
                        try:
                            self.game.mark_dirty_tile(tx, ty)
                        except Exception:
                            pass
    
    def _trigger_trap(self, trap: Dict[str, Any], actor: Any, pos: Tuple[int, int]) -> None:
        data = trap['data']
        effect = data.get('effect') or []
        tname = data.get('name', 'Trap')
        if not effect:
            self.game.log_event(f"{tname} triggers harmlessly.")
            return
        # Play trap-specific sound if available based on type/effect
        try:
            if hasattr(self.game, 'sound') and hasattr(self.game.sound, 'play_sfx'):
                ttype = data.get('type', '')
                # Map trap type/effect hints to sound keys
                sound_key = 'trap_trigger'
                type_map = {
                    'mechanical': 'trap_mechanical',
                    'magical': 'trap_magical',
                    'projectile': 'trap_projectile',
                    'fire': 'trap_fire',
                    'cold': 'trap_cold',
                    'shadow': 'trap_shadow',
                    'poison': 'trap_poison',
                }
                # Infer elemental from effect payload
                if isinstance(effect, list):
                    if 'fire' in effect:
                        sound_key = 'trap_fire'
                    elif 'cold' in effect:
                        sound_key = 'trap_cold'
                    elif 'poison' in effect or 'gas' in effect:
                        sound_key = 'trap_poison'
                # Override by explicit type mapping if present
                sound_key = type_map.get(ttype, sound_key)
                self.game.sound.play_sfx(sound_key)
        except Exception:
            pass
        etype = effect[0]
        if etype == 'damage' and len(effect) >= 2:
            dmg = _parse_damage_expr(effect[1])
            self._apply_trap_damage(actor, dmg, tname, data.get('damage_type', 'physical'))
            # Visual hit pulse
            try:
                self.game.add_spell_effect(pos, 'hit', duration=12)
            except Exception:
                pass
        elif etype == 'damage_status' and len(effect) >= 4:
            dmg = _parse_damage_expr(effect[1])
            status = effect[2]
            dur = int(effect[3])
            self.game.trap_manager._apply_trap_damage(actor, dmg, tname, data.get('damage_type', 'physical'))
            try:
                self.game.add_spell_effect(pos, 'hit', duration=14)
            except Exception:
                pass
            if actor is self.game.player:
                self.game._ensure_player_status_manager()
                if self.game.player and hasattr(self.game.player, 'status_manager'):
                    self.game.player.status_manager.add_effect(status, dur)
                self.game.log_event(f"You are {status.lower()}!")
            elif hasattr(actor, 'status_manager'):
                actor.status_manager.add_effect(status, dur)
        elif etype == 'area_damage' and len(effect) >= 3:
            dmg = _parse_damage_expr(effect[1])
            radius = int(effect[2])
            ax, ay = pos
            hits = 0
            for ent in self.game.entity_manager.entities:
                if ent.hp > 0:
                    ex, ey = ent.position
                    if (ex-ax)**2 + (ey-ay)**2 <= radius*radius:
                        edmg, _ = _apply_damage_modifiers(dmg, data.get('damage_type', 'physical'), ent)
                        ent.take_damage(edmg)
                        hits += 1
            if self.game.player and hasattr(self.game.player, 'position'):
                px, py = self.game.player.position
                if (px-ax)**2 + (py-ay)**2 <= radius*radius:
                    pdmg, _ = _apply_damage_modifiers(dmg, data.get('damage_type', 'physical'), self.game.player)
                    self.game._inflict_player_damage(pdmg, tname)
            self.game.log_event(f"{tname} erupts (hits {hits} + you maybe).")
            # Explosion visual
            try:
                self.game.add_spell_effect(pos, 'fire', duration=18)
            except Exception:
                pass
        elif etype == 'teleport' and len(effect) >= 2:
            rng = int(effect[1])
            if actor is self.game.player:
                self.game._teleport_player_random(rng)
            else:
                self.game._teleport_entity_random(actor, rng)
            self.game.log_event(f"{tname} blinks its victim!")
            try:
                self.game.add_spell_effect(pos, 'teleport', duration=16)
            except Exception:
                pass
        elif etype == 'alarm':
            for ent in self.game.entity_manager.entities:
                ent.aware_of_player = True
            self.game.log_event(f"{tname} rings loudly! Monsters are alerted.")
            # Small sparkles to show activation
            try:
                self.game.add_spell_effect(pos, 'magic', duration=10)
            except Exception:
                pass
        elif etype == 'area_status' and len(effect) >= 4:
            status_name = str(effect[1])
            duration = int(effect[2])
            radius = int(effect[3])
            ax, ay = pos
            affected = 0
            if self.game.player and hasattr(self.game.player, 'position'):
                px, py = self.game.player.position
                if (px-ax)**2 + (py-ay)**2 <= radius*radius:
                    self.game._ensure_player_status_manager()
                    self.game.player.status_manager.add_effect(status_name, duration)
                    affected += 1
                    self.game.log_event(f"You are affected by {tname}: {status_name.lower()}!")
            for ent in self.game.entity_manager.entities:
                if ent.hp > 0:
                    ex, ey = ent.position
                    if (ex-ax)**2 + (ey-ay)**2 <= radius*radius and hasattr(ent, 'status_manager'):
                        ent.status_manager.add_effect(status_name, duration)
                        affected += 1
            self.game.log_event(f"{tname} releases a cloud ({affected} affected).")
            # Cloud visual
            try:
                self.game.add_spell_effect(pos, 'debuff', duration=18)
            except Exception:
                pass
        elif etype == 'immobilize' and len(effect) >= 2:
            duration = int(effect[1])
            status_name = 'Immobilized'
            if actor is self.game.player:
                # Ensure the player has a status manager and guard against None
                self.game._ensure_player_status_manager()
                if self.game.player and hasattr(self.game.player, 'status_manager') and getattr(self.game.player, 'status_manager') is not None:
                    self.game.player.status_manager.add_effect(status_name, duration)
                    self.game.log_event("You are trapped in a net!")
            elif actor and hasattr(actor, 'status_manager') and getattr(actor, 'status_manager') is not None:
                actor.status_manager.add_effect(status_name, duration)
                self.game.log_event(f"{actor.name} is immobilized by {tname}!")
            try:
                self.game.add_spell_effect(pos, 'debuff', duration=12)
            except Exception:
                pass
        elif etype == 'line_damage' and len(effect) >= 3:
            dmg = _parse_damage_expr(effect[1])
            length = int(effect[2])
            ax, ay = pos
            hits = 0
            def in_cross(x:int,y:int)->bool:
                return (y==ay and abs(x-ax)<=length) or (x==ax and abs(y-ay)<=length)
            for ent in self.game.entity_manager.entities:
                if ent.hp>0:
                    ex, ey = ent.position
                    if in_cross(ex, ey):
                        ent.take_damage(dmg)
                        hits += 1
            if self.game.player and hasattr(self.game.player,'position'):
                px, py = self.game.player.position
                if in_cross(px, py):
                    self.game._inflict_player_damage(dmg, tname)
            self.game.log_event(f"{tname} slashes outward ({hits} + maybe you).")
            try:
                self.game.add_spell_effect(pos, 'hit', duration=10)
            except Exception:
                pass
        elif etype == 'elemental_bolt' and len(effect) >= 3:
            element = str(effect[1])
            dmg = _parse_damage_expr(effect[2])
            # Use element string directly as damage_type for modifiers (e.g., 'fire','cold','poison','lightning')
            self.game.trap_manager._apply_trap_damage(actor, dmg, tname, element.lower())
            self.game.log_event(f"A {element.lower()} bolt from {tname} strikes!")
            # Visual by element
            try:
                vis = 'lightning' if element.lower() == 'lightning' else (
                    'ice' if element.lower() in ('ice','frost','cold') else (
                    'fire' if element.lower() == 'fire' else 'magic'))
                self.game.add_spell_effect(pos, vis, duration=14)
            except Exception:
                pass
        elif etype == 'drop_level' and len(effect) >= 2:
            levels = int(effect[1])
            if actor is self.game.player:
                target_depth = self.game.current_depth + max(1, levels)
                self.game.log_event(f"{tname} drops you deeper!")
                self.game.change_depth(target_depth)
            else:
                try:
                    # Stage a death for the actor so that scheduled death effects are
                    # processed and the UI can display a death animation before removal.
                    actor.hp = 0
                    # Mark this death as not granting XP (fall-through shaft)
                    setattr(actor, '_death_no_xp', True)
                    # Process death logic (drops/xp) now, but do not remove entity.
                    self.game.entity_manager._process_entity_deaths()
                    self.game.log_event(f"{actor.name} falls through a shaft!")
                except Exception:
                    pass
        elif etype == 'summon' and len(effect) >= 3:
            template_id = str(effect[1])
            count = int(effect[2])
            ax, ay = pos
            spawned = 0
            for _ in range(count):
                candidates = [(ax+dx, ay+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1))]
                random.shuffle(candidates)
                placed = False
                for (nx, ny) in candidates:
                    if 0 <= nx < self.game.map_width and 0 <= ny < self.game.map_height and self.game.entity_manager.get_entity_at(nx, ny) is None:
                        tile = self.game.get_tile_at_coords(nx, ny)
                        if tile in (FLOOR, DOOR_OPEN, STAIRS_DOWN, STAIRS_UP):
                            try:
                                new_ent = Entity(template_id, self.game.current_depth, [nx, ny])
                                self.game.entity_manager.entities.append(new_ent)
                                spawned += 1
                                placed = True
                            except Exception:
                                pass
                            break
                if not placed:
                    break
            self.game.log_event(f"{tname} summons {spawned} creature(s)!")
            try:
                self.game.add_spell_effect(pos, 'magic', duration=12)
            except Exception:
                pass
        elif etype == 'chaos':
            choices = ['damage', 'teleport', 'alarm', 'immobilize']
            pick = random.choice(choices)
            self.game.log_event(f"{tname} warps with chaotic energy ({pick})!")
            if pick == 'damage':
                self._apply_trap_damage(actor, random.randint(3, 12), tname)
                try:
                    self.game.add_spell_effect(pos, 'hit', duration=12)
                except Exception:
                    pass
            elif pick == 'teleport':
                if actor is self.game.player:
                    self.game._teleport_player_random(8)
                else:
                    self.game._teleport_entity_random(actor, 8)
                try:
                    self.game.add_spell_effect(pos, 'teleport', duration=12)
                except Exception:
                    pass
            elif pick == 'alarm':
                for ent in self.game.entity_manager.entities:
                    ent.aware_of_player = True
                try:
                    self.game.add_spell_effect(pos, 'magic', duration=10)
                except Exception:
                    pass
            elif pick == 'immobilize':
                if actor is self.game.player:
                    self.game._ensure_player_status_manager()
                    if self.game.player and hasattr(self.game.player, 'status_manager') and getattr(self.game.player, 'status_manager') is not None:
                        self.game.player.status_manager.add_effect('Immobilized', 3)
                        try:
                            self.game.log_event("You are immobilized!")
                        except Exception:
                            pass
                elif actor and hasattr(actor, 'status_manager') and getattr(actor, 'status_manager') is not None:
                    actor.status_manager.add_effect('Immobilized', 3)
                    try:
                        self.game.log_event(f"{actor.name} is immobilized!")
                    except Exception:
                        pass
                try:
                    self.game.add_spell_effect(pos, 'debuff', duration=10)
                except Exception:
                    pass
        else:
            self.game.log_event(f"{tname} triggers with unknown magic.")

    def _apply_trap_damage(self, actor: Any, dmg: int, tname: str, damage_type: str = 'physical') -> None:
        """Apply trap damage with resistance/vulnerability modifiers.

        damage_type can be inferred by caller (e.g., 'fire', 'cold', 'poison').
        """
        # Apply modifiers
        final_dmg, resist_msg = _apply_damage_modifiers(dmg, damage_type, actor)
        if actor is self.game.player:
            dead = self.game._inflict_player_damage(final_dmg, tname)
            if dead:
                self.game.log_event(f"{tname} kills you!")
            else:
                msg = f"{tname} deals {final_dmg} damage"
                if resist_msg == 'resisted':
                    msg += " (resisted)"
                elif resist_msg == 'vulnerable':
                    msg += " (vulnerable)"
                msg += "."
                self.game.log_event(msg)
        else:
            if hasattr(actor, 'take_damage'):
                died = actor.take_damage(final_dmg)
                msg = f"{actor.name} is hit by {tname} for {final_dmg}"
                if resist_msg == 'resisted':
                    msg += " (resisted)"
                elif resist_msg == 'vulnerable':
                    msg += " (vulnerable)"
                msg += "."
                self.game.log_event(msg)
                if died:
                    actor.hp = 0
                    self.game.log_event(f"{actor.name} dies to {tname}.")