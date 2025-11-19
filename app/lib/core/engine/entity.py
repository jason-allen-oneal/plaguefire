import math
import random
from typing import List, Optional, Tuple

from app.lib.core.engine.pathfinding import find_path
from app.lib.core.logger import debug
from app.lib.utils import _apply_damage_modifiers, _get_status_effect_modifier, roll_dice
from app.model.entity import Entity
from app.model.status_effects import StatusEffectManager
from config import DOOR_CLOSED, DOOR_OPEN, FLOOR, SECRET_DOOR_FOUND, SECRET_DOOR, STAIRS_DOWN, STAIRS_UP


class EntityManager:
    entities: List[Entity] = []
    def __init__(self, game):
        self.game = game

        self.entities = []
        # Performance: spatial hash for O(1) entity lookups by position
        self._spatial_hash: dict[Tuple[int, int], Entity] = {}
    
    def _is_walkable_for_ai(self, x: int, y: int) -> bool:
        if not (0 <= x < self.game.map_width and 0 <= y < self.game.map_height):
            return False
        if not self.game.current_map:
            return False
        tile = self.game.current_map[y][x]
        # AI can path through floors, stairs, and open doors only.
        # Closed doors and secret doors must be opened first and are not considered walkable for pathfinding.
        if tile not in (FLOOR, STAIRS_DOWN, STAIRS_UP, DOOR_OPEN):
            return False
        if self.get_entity_at(x, y):
            return False
        # Treat player's tile as non-walkable for AI (they attack instead)
        if self.game.player and hasattr(self.game.player, 'position') and tuple(self.game.player.position) == (x, y):
            return False
        return True

    def _approach(self, entity: Entity, px: int, py: int) -> None:
        ex, ey = entity.position
        path = find_path(self.game.map_width, self.game.map_height, (ex, ey), (px, py), self._is_walkable_for_ai, max_nodes=500)
        if path:
            debug(f"[AI][APPROACH] {entity.name} path_len={len(path)} next={path[0]} target=({px},{py})")
            nx, ny = path[0]
            if [nx, ny] != [px, py]:
                self._move_entity(entity, nx, ny)
            else:
                # Adjacent -> attack
                debug(f"[AI][APPROACH] {entity.name} adjacent -> attack player")
                self._entity_attack(entity)
        else:
            debug(f"[AI][APPROACH] {entity.name} no path -> naive step toward player")
            # Fallback naive step
            dx = 0 if px == ex else (1 if px > ex else -1)
            dy = 0 if py == ey else (1 if py > ey else -1)
            nx, ny = ex + dx, ey + dy
            if self._is_walkable_for_ai(nx, ny):
                debug(f"[AI][APPROACH] {entity.name} naive move ({ex},{ey})->({nx},{ny})")
                self._move_entity(entity, nx, ny)
            else:
                debug(f"[AI][APPROACH] {entity.name} naive blocked target=({nx},{ny})")

    
    def _wander_entity(self, entity: Entity) -> None:
        ex, ey = entity.position
        for _ in range(4):
            dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
            nx, ny = ex + dx, ey + dy
            if self._is_walkable_for_ai(nx, ny):
                debug(f"[AI][WANDER] {entity.name} move ({ex},{ey})->({nx},{ny})")
                self._move_entity(entity, nx, ny)
                break
        else:
            debug(f"[AI][WANDER] {entity.name} no valid move from ({ex},{ey})")

    def _aggressive_entity(self, entity: Entity, dist: float, px: int, py: int) -> None:
        """
        Enhanced aggressive AI with tactical combat decisions.
        - Smarter fleeing based on HP and distance
        - Uses terrain and distance to choose ranged vs melee
        - Maintains pressure while managing health
        """
        ex, ey = entity.position
        
        # Dynamic fleeing with better logic
        if entity.status_manager.has_behavior('flee'):
            debug(f"[AI][AGG] {entity.name} fleeing dist={dist:.2f}")
            # Flee away from player, prefer longer escape routes
            flee_options = []
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                nx, ny = ex + dx, ey + dy
                if self._is_walkable_for_ai(nx, ny):
                    # Score based on distance gained from player
                    new_dist = math.sqrt((nx - px)**2 + (ny - py)**2)
                    flee_options.append(((nx, ny), new_dist))
            
            if flee_options:
                # Pick position that maximizes distance from player
                best_flee = max(flee_options, key=lambda x: x[1])
                nx, ny = best_flee[0]
                self._move_entity(entity, nx, ny)
            else:
                # Fallback
                dx = 0 if px == ex else (-1 if px > ex else 1)
                dy = 0 if py == ey else (-1 if py > ey else 1)
                nx, ny = ex + dx, ey + dy
                if self._is_walkable_for_ai(nx, ny):
                    self._move_entity(entity, nx, ny)
            return
        
        if not entity.aware_of_player:
            debug(f"[AI][AGG] {entity.name} not aware; skip combat logic dist={dist:.2f}")
            return
        
        # Tactical ranged/spell usage based on distance and HP
        hp_percent = entity.hp / max(1, entity.max_hp)
        prefer_ranged = hp_percent < 0.5  # Prefer ranged when wounded
        
        if dist > 1.5:
            acted = False
            # Wounded enemies prefer ranged combat
            ranged_chance = 0.70 if prefer_ranged else 0.55
            
            if entity.ranged_attack and dist <= entity.ranged_range and self.game.fov._line_of_sight(ex, ey, px, py):
                if random.random() < ranged_chance:
                    self._entity_ranged_attack(entity, px, py, dist)
                    acted = True
                    debug(f"[AI][AGG] {entity.name} uses ranged attack dist={dist:.2f}")
            
            if not acted and entity.spell_list and entity.mana > 0:
                spell_chance = 0.50 if prefer_ranged else 0.35
                if random.random() < spell_chance:
                    if self._entity_cast_spell(entity, px, py, dist):
                        acted = True
                        debug(f"[AI][AGG] {entity.name} casts spell dist={dist:.2f}")
            
            # If ranged attack used, consider maintaining distance
            if acted and prefer_ranged and dist < 4:
                # Back up slightly after ranged attack
                debug(f"[AI][AGG] {entity.name} acted ranged+prefer_ranged; holding position dist={dist:.2f}")
                return
            elif acted:
                debug(f"[AI][AGG] {entity.name} acted (ranged/spell); end turn dist={dist:.2f}")
                return
        
        # Melee engagement
        if dist <= 1.5:
            debug(f"[AI][AGG] {entity.name} melee attack dist={dist:.2f}")
            self._entity_attack(entity)
        else:
            debug(f"[AI][AGG] {entity.name} approaches player dist={dist:.2f}")
            self._approach(entity, px, py)

    def _pack_entity(self, entity: Entity, dist: float, px: int, py: int) -> None:
        """
        Enhanced pack AI with coordination, morale, and tactics.
        - Allies boost morale and reduce flee chance
        - Pack members call for help when engaging
        - Coordinate to surround player when possible
        - Retreat together when morale breaks
        """
        ex, ey = entity.position
        
        # Count nearby allies (same template_id within detection range)
        ally_count = 0
        allies_nearby = []
        for other in self.entities:
            if other.hp > 0 and other.template_id == entity.template_id and other != entity:
                ox, oy = other.position
                ally_dist = math.sqrt((ex - ox)**2 + (ey - oy)**2)
                if ally_dist <= entity.detection_range:
                    ally_count += 1
                    allies_nearby.append(other)
        
        # Dynamic fleeing based on morale (HP% + ally presence)
        hp_percent = entity.hp / max(1, entity.max_hp)
        morale_threshold = 0.25 + (ally_count * 0.1)  # Higher with allies
        
        if hp_percent < morale_threshold and not entity.status_manager.has_behavior('flee'):
            flee_chance = int((1 - hp_percent) * 100)
            # Allies reduce flee chance
            flee_chance = max(10, flee_chance - (ally_count * 15))
            if random.randint(1, 100) <= flee_chance:
                entity.status_manager.add_effect('Fleeing', 10 + ally_count * 2)
                self.game.log_event(f"{entity.name} retreats!")
                # Signal allies to consider retreat
                for ally in allies_nearby:
                    if ally.hp / max(1, ally.max_hp) < 0.4 and random.random() < 0.3:
                        ally.status_manager.add_effect('Fleeing', 8)
        
        if entity.status_manager.has_behavior('flee'):
            # Coordinated retreat: try to move toward nearest ally or away from player
            if allies_nearby:
                # Move toward nearest healthy ally
                nearest_ally = min(allies_nearby, key=lambda a: math.sqrt((ex - a.position[0])**2 + (ey - a.position[1])**2))
                target_x, target_y = nearest_ally.position
            else:
                # Just flee away from player
                target_x = ex - (1 if px > ex else -1 if px < ex else 0)
                target_y = ey - (1 if py > ey else -1 if py < ey else 0)
            
            if target_x != ex or target_y != ey:
                dx = 0 if target_x == ex else (1 if target_x > ex else -1)
                dy = 0 if target_y == ey else (1 if target_y > ey else -1)
                nx, ny = ex + dx, ey + dy
                if self._is_walkable_for_ai(nx, ny):
                    self._move_entity(entity, nx, ny)
            return
        
        # Awareness and calling for help
        if not entity.aware_of_player and dist <= entity.detection_range and self.game.fov._line_of_sight(ex, ey, px, py):
            entity.aware_of_player = True
            # Call for help - alert nearby sleeping/unaware allies
            if ally_count > 0:
                for ally in allies_nearby:
                    if not ally.aware_of_player and random.random() < 0.7:
                        ally.aware_of_player = True
                        ally.is_sleeping = False  # Wake up!
                if random.random() < 0.4:
                    self.game.log_event(f"{entity.name} howls for the pack!")
        
        if not entity.aware_of_player:
            return
        
        # Pack ranged/spell support
        if dist > 1.5:
            if entity.ranged_attack and dist <= entity.ranged_range and self.game.fov._line_of_sight(ex, ey, px, py):
                if random.random() < 0.50:  # Increased ranged usage
                    self._entity_ranged_attack(entity, px, py, dist)
                    return
            if entity.spell_list and entity.mana > 0 and random.random() < 0.30:
                if self._entity_cast_spell(entity, px, py, dist):
                    return
        
        # Melee: attempt to surround player
        if dist <= 1.5:
            self._entity_attack(entity)
        else:
            # Surround tactics: if allies are engaging, try to flank
            if ally_count >= 2 and dist <= 4:
                # Find position adjacent to player not occupied by allies
                surround_positions = [
                    (px + dx, py + dy)
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
                ]
                # Filter walkable positions not occupied by allies
                open_flanks = [
                    pos for pos in surround_positions
                    if self._is_walkable_for_ai(pos[0], pos[1]) and not self.get_entity_at(pos[0], pos[1])
                ]
                if open_flanks:
                    # Pick closest flank position
                    target = min(open_flanks, key=lambda p: abs(p[0] - ex) + abs(p[1] - ey))
                    self._approach(entity, target[0], target[1])
                    return
            # Default: approach directly
            self._approach(entity, px, py)

    def _thief_entity(self, entity: Entity, dist: float, px: int, py: int) -> None:
        """
        Enhanced thief AI with stealth, ambush, and tactical theft.
        - Hides in shadows (unlit tiles) to ambush
        - Attempts theft then flees
        - Uses ranged attacks from stealth
        - Repositions to stay out of direct sight
        """
        ex, ey = entity.position
        
        # Check if thief is in shadows (not in visible light)
        in_shadows = True
        if hasattr(self, 'visibility') and 0 <= ey < len(self.game.fov.visibility) and 0 <= ex < len(self.game.fov.visibility[0]):
            in_shadows = self.game.fov.visibility[ey][ex] != 2  # Not currently visible to player
        
        # Fleeing after theft
        if entity.status_manager.has_behavior('flee'):
            # Try to hide in nearest shadow while fleeing
            escape_options = []
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                nx, ny = ex + dx, ey + dy
                if self._is_walkable_for_ai(nx, ny):
                    # Prefer darker tiles
                    tile_visibility = 0
                    if hasattr(self, 'visibility') and 0 <= ny < len(self.game.fov.visibility) and 0 <= nx < len(self.game.fov.visibility[0]):
                        tile_visibility = self.game.fov.visibility[ny][nx]
                    # Prefer moving away from player AND into shadows
                    away_score = abs(nx - px) + abs(ny - py)
                    shadow_bonus = 3 if tile_visibility < 2 else 0
                    escape_options.append(((nx, ny), away_score + shadow_bonus))
            
            if escape_options:
                best_escape = max(escape_options, key=lambda x: x[1])
                nx, ny = best_escape[0]
                self._move_entity(entity, nx, ny)
            else:
                # Fallback: just move away
                dx = 0 if px == ex else (-1 if px > ex else 1)
                dy = 0 if py == ey else (-1 if py > ey else 1)
                nx, ny = ex + dx, ey + dy
                if self._is_walkable_for_ai(nx, ny):
                    self._move_entity(entity, nx, ny)
            return
        
        # Stealth detection (harder to spot in shadows)
        detection_mod = 0.5 if in_shadows else 1.0
        effective_detection_range = entity.detection_range * detection_mod
        
        if dist <= effective_detection_range and self.game.fov._line_of_sight(ex, ey, px, py):
            if not entity.aware_of_player and random.random() < detection_mod:
                entity.aware_of_player = True
        
        if not entity.aware_of_player:
            # Stealth mode: try to position for ambush
            if dist <= entity.detection_range * 1.5:
                # Try to circle around to flank
                flank_positions = [
                    (px + dx, py + dy)
                    for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                ]
                valid_flanks = [
                    pos for pos in flank_positions
                    if self._is_walkable_for_ai(pos[0], pos[1])
                ]
                if valid_flanks:
                    target = min(valid_flanks, key=lambda p: abs(p[0] - ex) + abs(p[1] - ey))
                    self._approach(entity, target[0], target[1])
                    return
            return
        
        # Ambush: ranged attack from stealth
        if in_shadows and dist > 1.5 and dist <= entity.ranged_range:
            if entity.ranged_attack and self.game.fov._line_of_sight(ex, ey, px, py):
                if random.random() < 0.70:  # High chance from stealth
                    self._entity_ranged_attack(entity, px, py, dist)
                    if random.random() < 0.4:
                        self.game.log_event(f"{entity.name} strikes from the shadows!")
                    return
        
        # Close range: theft attempt
        if dist <= 1.5:
            # Theft attempt
            if getattr(self.game.player, 'gold', 0) > 0 and random.random() < 0.60 and self.game.player:
                current_gold = getattr(self.game.player, 'gold', 0)
                # Better thieves steal more
                thief_skill = getattr(entity, 'level', 1)
                stolen = min(random.randint(thief_skill, thief_skill * 3), current_gold)
                try:
                    self.game.player.gold = max(0, current_gold - stolen)
                except Exception:
                    stolen = 0
                self.game.log_event(f"{entity.name} steals {stolen} gold!")
                entity.status_manager.add_effect('Fleeing', 15 + thief_skill)
            elif random.random() < 0.3:
                # Sometimes attack instead of stealing
                self._entity_attack(entity)
                if random.random() < 0.5:
                    entity.status_manager.add_effect('Fleeing', 10)
            else:
                self.game.log_event(f"{entity.name} fails to steal from you!")
                entity.status_manager.add_effect('Fleeing', 12)
        else:
            # Approach cautiously, trying to stay in shadows when possible
            if in_shadows and dist <= 4:
                # Stay hidden, circle closer
                circle_positions = [
                    (px + dx, py + dy)
                    for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                ]
                valid_circles = [
                    pos for pos in circle_positions
                    if self._is_walkable_for_ai(pos[0], pos[1]) and abs(pos[0] - ex) + abs(pos[1] - ey) <= 2
                ]
                if valid_circles:
                    target = random.choice(valid_circles)
                    self._approach(entity, target[0], target[1])
                    return
            # Default approach is now gated by a pursuit check
            if self._should_pursue_thief(dist):
                debug(f"[AI][THIEF] {entity.name} chooses to pursue the player")
                self._approach(entity, px, py)
            else:
                # Prefer to hold or slip into darker tiles away from player
                debug(f"[AI][THIEF] {entity.name} decides not to pursue; staying hidden")
                moved = False
                best_opt = None
                best_score = None
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                    nx, ny = ex + dx, ey + dy
                    if not self._is_walkable_for_ai(nx, ny):
                        continue
                    # Prefer tiles that are darker and slightly farther from player
                    vis = 2
                    if hasattr(self, 'visibility') and 0 <= ny < len(self.game.fov.visibility) and 0 <= nx < len(self.game.fov.visibility[0]):
                        vis = self.game.fov.visibility[ny][nx]
                    away = abs(nx - px) + abs(ny - py)
                    score = away + (2 - vis)  # higher is better (darker and farther)
                    if best_score is None or score > best_score:
                        best_score = score
                        best_opt = (nx, ny)
                if best_opt:
                    self._move_entity(entity, best_opt[0], best_opt[1])
                    moved = True
                if not moved:
                    # Idle
                    pass

    # Pursuit decision helpers
    def _should_pursue_beggar(self, dist: float) -> bool:
        """Decide if a beggar chooses to pursue the player.
        Factors: player gold, distance, and time of day.
        """
        pgold = getattr(self.game.player, 'gold', 0) if self.game.player else 0
        if pgold <= 0:
            return False
        base = 0.45  # baseline when you have gold
        if dist < 5:
            base += 0.20
        if not self.game.fov._is_daytime():
            base += 0.10
        return random.random() < min(0.85, base)

    def _should_pursue_thief(self, dist: float) -> bool:
        """Decide if a thief chooses to actively pursue the player.
        Factors: player gold, distance, and time of day.
        """
        pgold = getattr(self.game.player, 'gold', 0) if self.game.player else 0
        base = 0.25
        if pgold > 50:
            base += 0.25
        elif pgold > 0:
            base += 0.15
        if not self.game.fov._is_daytime():
            base += 0.15
        if dist < 6:
            base += 0.10
        return random.random() < min(0.9, base)

    def _entity_attack(self, entity: Entity) -> None:
        """Entity melee attack against player with full equipment bonuses."""
        roll = random.randint(1, 20)
        entity_attack_bonus = getattr(entity, 'attack', 0)
        status_modifier = _get_status_effect_modifier(entity, "attack")
        attack_total = roll + entity_attack_bonus + status_modifier
        
        # Use player's total AC including equipment
        player_ac = self.game.player.get_total_ac() if self.game.player else 10
        
        ex, ey = entity.position
        
        if roll == 1 or attack_total < player_ac:
            self.game.log_event(f"{entity.name} misses.")
            # Small noise even on miss
            self.game.noise_manager.create_noise((ex, ey), radius=3, intensity=1)
            return
        
        base_dmg = max(1, entity.attack // 2)
        damage_status_modifier = _get_status_effect_modifier(entity, "damage")
        dmg = (base_dmg * 2 if roll == 20 else base_dmg) + damage_status_modifier
        dmg = max(1, dmg)  # Ensure at least 1 damage
        
        # Get entity attack damage type (default to physical)
        entity_template = self.game.loader.get_entity(entity.template_id)
        damage_type = entity_template.get('damage_type', 'physical') if entity_template else 'physical'
        
        # Apply resistance/vulnerability modifiers
        final_dmg, resist_msg = _apply_damage_modifiers(dmg, damage_type, self.game.player)
        
        # Combat creates noise (wakes nearby sleepers)
        noise_intensity = 5 if roll != 20 else 8  # Crits are louder
        self.game.noise_manager.create_noise((ex, ey), radius=5, intensity=noise_intensity)
        
        # Add visual effect on player position when hit
        if self.game.player and hasattr(self.game.player, 'position'):
            px, py = self.game.player.position
            impact_duration = 15 if roll == 20 else 12
            self.game.add_spell_effect((px, py), 'hit', duration=impact_duration)
        
        dead = self.game._inflict_player_damage(final_dmg, entity.name, show_effect=False)
        if dead:
            self.game.log_event(f"{entity.name} strikes you down!")
        else:
            dmg_msg = f"{entity.name} hits you for {final_dmg} dmg"
            if resist_msg == "resisted":
                dmg_msg += " (resisted)"
            elif resist_msg == "vulnerable":
                dmg_msg += " (vulnerable)"
            dmg_msg += "."
            self.game.log_event(dmg_msg)

    # -------------------------
    # Ranged & Spell Attacks
    # -------------------------
    def _entity_ranged_attack(self, entity: Entity, px: int, py: int, dist: float) -> None:
        data = entity.ranged_attack
        if not data:
            return
        dmg_expr = data.get('damage', '1d4')
        dmg = self.game._parse_damage_expr(dmg_expr)
        # Spawn a travelling projectile; damage is applied on impact during projectile update
        start = (entity.position[0], entity.position[1])
        end = (px, py)
        # Visual projectile type heuristic based on data name
        pname = str(data.get('name', '')).lower()
        if 'crossbow' in pname or 'bolt' in pname:
            ptype = 'crossbow_bolt'
        elif 'sling' in pname or 'bullet' in pname:
            ptype = 'sling_bullet'
        elif 'javelin' in pname:
            ptype = 'javelin'
        elif 'tomahawk' in pname:
            ptype = 'tomahawk'
        elif 'dart' in pname:
            ptype = 'dart'
        elif 'rock' in pname or 'stone' in pname:
            ptype = 'stone_arrow'
        elif 'arrow' in pname or 'bow' in pname:
            ptype = 'arrow'
        else:
            ptype = 'arrow'
        self.game.add_visual_projectile(start, end, ptype, speed=0.45)
        self.game._spawn_projectile(start, end, dmg, kind='ranged', source='entity', on_hit_msg=f"{entity.name}'s {data.get('name','ranged')} hits you for {dmg}!", impact_effect_type='hit', impact_duration=10)
        self.game.log_event(f"{entity.name} fires {data.get('name','ranged')}.")

    def _entity_cast_spell(self, entity: Entity, px: int, py: int, dist: float) -> bool:
        if not entity.spell_list or entity.mana <= 0:
            return False
        # Filter castable spells (enough mana, appropriate distance)
        viable = []
        for sid in entity.spell_list:
            sp = self.game.loader.get_spell(sid)
            if not sp:
                continue
            # Use a simple mana cost inference based on presence of 'classes' -> treat first entry's mana as cost
            mana_cost = 0
            classes = sp.get('classes') or {}
            if classes:
                first_class = next(iter(classes.values()))
                mana_cost = first_class.get('mana', 0)
            if mana_cost > entity.mana:
                continue
            # Range heuristic: attack spells require LOS and dist <= 10; buffs always cast; others need LOS if requires_target
            if sp.get('effect_type') in ('attack','debuff') and not self.game.fov._line_of_sight(entity.position[0], entity.position[1], px, py):
                continue
            if sp.get('requires_target') and dist > 10:
                continue
            viable.append((sp, mana_cost))
        if not viable:
            return False
        sp, mana_cost = random.choice(viable)
        entity.mana -= mana_cost
        etype = sp.get('effect_type')
        name = sp.get('name','Spell')
        if etype == 'attack':
            dmg_expr = sp.get('damage','2d4')
            dmg = self.game._parse_damage_expr(dmg_expr)
            dead = self.game._inflict_player_damage(dmg, f"{entity.name} ({name})")
            if dead:
                self.game.log_event(f"{entity.name}'s {name} annihilates you for {dmg}!")
            else:
                self.game.log_event(f"{entity.name} casts {name} for {dmg} dmg.")
            # Noise from offensive spell
            ex, ey = entity.position
            self.game.noise_manager.create_noise((ex, ey), radius=6, intensity=6)
        elif etype == 'buff':
            status = sp.get('status','Buffed')
            dur = sp.get('duration', 25)
            # Use centralized application (respects immunities)
            self.game._apply_status_effect(entity, status, duration=dur, source=name)
            self.game.log_event(f"{entity.name} casts {name} and becomes {status}.")
            # Noise from buff spell (quieter)
            ex, ey = entity.position
            self.game.noise_manager.create_noise((ex, ey), radius=5, intensity=4)
        elif etype == 'debuff':
            status = sp.get('status','Debuffed')
            dur = sp.get('duration', 20)
            # Lazy init player status manager
            if self.game.player and not hasattr(self.game.player, 'status_manager'):
                self.game.player.status_manager = StatusEffectManager()
            if self.game.player:
                self.game._apply_status_effect(self.game.player, status, duration=dur, source=f"{entity.name}:{name}")
            self.game.log_event(f"{entity.name} casts {name}; you are afflicted with {status}!")
            # Noise from debuff spell
            ex, ey = entity.position
            self.game.noise_manager.create_noise((ex, ey), radius=6, intensity=6)
        elif etype == 'heal':
            amt = sp.get('heal_amount', 10)
            healed_before = entity.hp
            entity.hp = min(entity.max_hp, entity.hp + amt)
            self.game.log_event(f"{entity.name} casts {name} and heals {entity.hp - healed_before} HP.")
            # Minimal noise for healing
            ex, ey = entity.position
            self.game.noise_manager.create_noise((ex, ey), radius=4, intensity=3)
        elif etype == 'teleport':
            rng = sp.get('range', 6)
            self.game._teleport_entity_random(entity, rng)
            self.game.log_event(f"{entity.name} blinks away with {name}!")
            # Blink has a sharp pop
            ex, ey = entity.position
            self.game.noise_manager.create_noise((ex, ey), radius=5, intensity=5)
        else:
            # Generic utility (ignore effect for now)
            self.game.log_event(f"{entity.name} casts {name}.")
        return True
    
    # -------------------------
    # Entity Death & Drops
    # -------------------------
    def _process_entity_deaths(self):
        if not self.game.player:
            return
        for e in self.entities[:]:
            # Skip alive entities or those we already processed
            if e.hp > 0 or getattr(e, '_death_processed', False):
                continue
            setattr(e, '_death_processed', True)
            x, y = e.position
            drops, gold_amt = e.get_drops() if hasattr(e, 'get_drops') else ([], 0)
            
            # Check for ammo recovery from ranged kills
            if hasattr(self, '_last_fired_ammo') and self.game._last_fired_ammo:
                target_pos = self.game._last_fired_ammo.get('target_pos')
                if target_pos == (x, y):
                    # 50% chance to recover ammunition
                    if random.random() < 0.5:
                        ammo_id = self.game._last_fired_ammo['item_id']
                        ammo_name = self.game._last_fired_ammo['item_name']
                        drops.append(ammo_id)
                        self.game.log_event(f'You recover a {ammo_name}.')
                    # Clear the last fired ammo
                    self.game._last_fired_ammo = None
            
            if drops or gold_amt:
                entry = {'pos': (x, y), 'items': drops, 'gold': gold_amt, 'name': e.name, 'turn': self.game.time}
                self.game.death_drop_log.append(entry)
            # Place items on ground
            if drops:
                pile = self.game.ground_items.setdefault((x, y), [])
                pile.extend(drops)
            if gold_amt > 0:
                pile = self.game.ground_items.setdefault((x, y), [])
                pile.append(f"GOLD:{gold_amt}")
            # Award XP unless the death is marked as not providing XP (e.g., poison or trap falls)
            if not getattr(e, '_death_no_xp', False):
                xp_gain = self._compute_xp_reward(e)
                leveled = self.game.player.gain_xp(xp_gain)
                self.game.log_event(f"You slay {e.name}! (+{xp_gain} XP)")
            else:
                # Still log, but do not grant XP
                self.game.log_event(f"{e.name} dies.")
            if leveled:
                self.game.log_event(f"You reach level {self.game.player.level}!")
            # Stage death for visual removal: mark entity as dying and allow
            # MapView to handle actual removal once the death animation completes.
            try:
                e.is_dying = True
                e.death_animation_frame = 0
                debug(f"[ENTITY] Marked {e.name} as dying (frame reset to 0)")
            except Exception:
                pass

    # -------------------------
    # Cloning System
    # -------------------------
    def _attempt_entity_clone(self, entity: Entity):
        if entity.clone_rate <= 0 or entity.hp <= 0 or not self.game.current_map:
            return
        # Count existing of same template
        same = sum(1 for e in self.entities if e.template_id == entity.template_id and e.hp > 0)
        if entity.clone_max_population and same >= entity.clone_max_population:
            return
        if random.random() >= entity.clone_rate:
            return
        # Find adjacent walkable tile
        ex, ey = entity.position
        candidates = [(ex+dx, ey+dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))]
        random.shuffle(candidates)
        for nx, ny in candidates:
            if self._is_walkable_for_ai(nx, ny):
                try:
                    new_ent = Entity(entity.template_id, self.game.current_depth, [nx, ny])
                    self.entities.append(new_ent)
                    # Performance: update spatial hash for new entity
                    self._spatial_hash[(nx, ny)] = new_ent
                    self.game.log_event(f"{entity.name} divides!")
                except Exception:
                    pass
                return
    
    def _move_entity(self, entity: Entity, x: int, y: int) -> None:
        """Move an entity if destination is walkable and unoccupied.

        Prevents moving onto walls, other entities, or the player tile.
        Automatically opens closed doors when AI moves through them.
        """
        # Trap-induced immobilization: block movement if Immobilized status active
        try:
            if hasattr(entity, 'status_manager') and getattr(entity.status_manager, 'has_effect', None) and entity.status_manager.has_effect('Immobilized'):
                self.game.log_event(f"{entity.name} is immobilized and cannot move!")
                return
        except Exception:
            pass
        if not self.game.current_map:
            return
        if not (0 <= x < self.game.map_width and 0 <= y < self.game.map_height):
            return
        tile = self.game.current_map[y][x]
        
        # Check if tile is a closed door or revealed secret door - AI may open it
        # AI cannot open unrevealed secret doors (SECRET_DOOR)
        if tile == DOOR_CLOSED or tile == SECRET_DOOR_FOUND:
            # Only allow auto-opening for entities that can manipulate doors (humanoids with
            # appropriate intelligence/appendages). Templates can explicitly opt-in/out using
            # the `can_open_doors` flag. If not allowed, treat the door as blocking movement.
            if not self._can_entity_open_doors(entity):
                debug(f"[AI][DOOR] {entity.name} cannot open door at ({x},{y}) - blocked")
                return
            # Open the door (opening consumes the AI's action)
            self.game.current_map[y][x] = DOOR_OPEN
            self.game.log_event(f"{entity.name} opens a door.")
            self.game.noise_manager.create_noise((x, y), radius=2, intensity=2)
            self.game.fov.update_fov()
            debug(f"[AI][DOOR] {entity.name} opened door at ({x},{y})")
            try:
                self.game.mark_dirty_tile(x, y)
            except Exception:
                pass
            # Don't move yet - door opening takes their action this turn
            return
        
        # Normal walkability check
        if tile not in (FLOOR, STAIRS_DOWN, STAIRS_UP, DOOR_OPEN):
            debug(f"[AI][MOVE] {entity.name} blocked by tile {tile} at ({x},{y})")
            return
        # Block if another entity occupies target
        if self.get_entity_at(x, y):
            debug(f"[AI][MOVE] {entity.name} blocked by entity at ({x},{y})")
            return
        # Block if player occupies target
        if self.game.player and hasattr(self.game.player, 'position') and tuple(self.game.player.position) == (x, y):
            debug(f"[AI][MOVE] {entity.name} blocked by player at ({x},{y})")
            return
        prev: Tuple[int, int] = (entity.position[0], entity.position[1])
        # Update sprite direction based on movement
        dx, dy = x - prev[0], y - prev[1]
        if dy < 0:
            entity._sprite_direction = 'up'
        elif dy > 0:
            entity._sprite_direction = 'down'
        elif dx < 0:
            entity._sprite_direction = 'left'
        elif dx > 0:
            entity._sprite_direction = 'right'
        
        # Performance: update spatial hash when entity moves
        if prev in self._spatial_hash and self._spatial_hash[prev] == entity:
            del self._spatial_hash[prev]
        
        # Always assign tuple for consistency
        entity.position = (x, y)
        self._spatial_hash[(x, y)] = entity
        
        debug(f"[AI][MOVE] {entity.name} {prev}->({x},{y})")
        self.game._on_actor_moved(entity, prev, (x, y))
    
    # -------------------------
    # Entity / AI Processing
    # -------------------------
    def get_entity_at(self, x: int, y: int) -> Optional[Entity]:
        # Performance: O(1) hash lookup instead of O(n) linear search
        entity = self._spatial_hash.get((x, y))
        if entity and not getattr(entity, 'is_dying', False):
            return entity
        return None

    def remove_entity(self, entity: Entity) -> None:
        """Remove an entity from tracking and mark its tile dirty for redraw."""
        if entity in self.entities:
            self.entities.remove(entity)
        try:
            pos = (int(entity.position[0]), int(entity.position[1]))
        except Exception:
            pos = getattr(entity, 'position', (None, None))
        if pos in self._spatial_hash and self._spatial_hash.get(pos) is entity:
            del self._spatial_hash[pos]
        if hasattr(self.game, 'mark_dirty_tile') and all(isinstance(c, int) for c in pos if c is not None):
            try:
                self.game.mark_dirty_tile(pos[0], pos[1])
            except Exception:
                pass

    def _can_entity_open_doors(self, entity: Entity) -> bool:
        """Heuristic: decide whether an AI entity can auto-open doors.

        Rules applied (in order):
        - If the entity's template explicitly contains `can_open_doors` (bool), use that.
        - If the entity has tags that strongly disqualify manipulation (undead, construct,
          ooze, elemental, plant, insect, snake, ghost), return False.
        - If the template id/name contains common humanoid keywords, and the entity shows
          signs of enough "intelligence" (spell list, ranged attack, or non-trivial ai_type),
          allow. Otherwise disallow.

        This is intentionally conservative and can be overridden per-entity via the
        `can_open_doors` template flag in `data/entities.json`.
        """
        tpl = self.game.loader.get_entity(entity.template_id) or {}
        # Explicit template override
        if 'can_open_doors' in tpl:
            return bool(tpl.get('can_open_doors'))

        # Disqualifying tags (if present on entity.templates)
        disqualify = {'undead', 'construct', 'ooze', 'elemental', 'plant', 'insect', 'snake', 'ghost'}
        for t in getattr(entity, 'tags', []) or []:
            if str(t).lower() in disqualify:
                return False

        # Humanoid/name heuristics
        name_id = (entity.template_id or '').upper()
        humanoid_keywords = (
            'HUMAN','CITIZEN','GUARD','BRIGAND','MERCHANT','PRIEST','PALADIN','KNIGHT',
            'WARRIOR','VETERAN','ROGUE','ORC','GOBLIN','ELF','DWARF','HALFLING','GNOME',
            'SOLDIER','MERCENARY','BANDIT','THIEF','CITIZEN','TOWN'
        )
        is_humanoid = any(k in name_id for k in humanoid_keywords)

        if not is_humanoid:
            return False

        # Intelligence/appendage heuristics: presence of spell list, ranged attack, or
        # active AI types imply purposeful agents capable of manipulating doors.
        intelligence_ok = bool(getattr(entity, 'spell_list', [])) or bool(getattr(entity, 'ranged_attack', None))
        if not intelligence_ok:
            # Consider ai_type as a weak proxy (thief/pack/aggressive/wander implies goal-directed behavior)
            if getattr(entity, 'ai_type', '') in ('aggressive', 'pack', 'thief', 'wander'):
                intelligence_ok = True

        return bool(is_humanoid and intelligence_ok)

    def update_entities(self) -> None:
        # Early diagnostics to understand why AI might be skipped
        if not self.game.player:
            debug("[AI] Skipped entity update: no player")
            return
        if not self.game.current_map:
            debug("[AI] Skipped entity update: no current_map")
            return
        if not self.entities:
            debug("[AI] Skipped entity update: no entities present")
            return
        debug(f"[AI] Updating {len(self.entities)} entities")
        px, py = getattr(self.game.player, 'position', (0, 0))
        
        # Performance: skip full AI updates for distant entities
        # Only process entities within reasonable distance from player
        AI_UPDATE_DISTANCE = 20  # Tune this value based on map size
        
        entities_processed = 0
        entities_skipped = 0
        
        for entity in self.entities[:]:
            # Advance death animations/cleanup for dead entities so they do not linger
            if entity.hp <= 0:
                # If death already processed (drops/xp), advance timer toward removal
                if getattr(entity, '_death_processed', False):
                    entity.is_dying = True
                    entity.death_animation_frame = getattr(entity, 'death_animation_frame', 0) + 1
                    if entity.death_animation_frame >= getattr(entity, 'death_animation_duration', 12):
                        self.remove_entity(entity)
                continue
            
            # Calculate distance to player early for culling
            ex, ey = entity.position
            dist = math.sqrt((ex - px) ** 2 + (ey - py) ** 2)
            
            # Performance: skip AI updates for distant entities unless they're aware of player
            # Always tick status effects and sleep state for all entities
            if dist > AI_UPDATE_DISTANCE and not entity.aware_of_player:
                # Still tick status effects even for distant entities
                if hasattr(entity, 'status_manager'):
                    entity.status_manager.tick_effects()
                # Update sleep state
                time_of_day = 'Day' if self.game.fov._is_daytime() else 'Night'
                entity.update_sleep_state(time_of_day)
                entities_skipped += 1
                continue
            
            entities_processed += 1
            
            # Per-entity diagnostic summary
            debug(
                f"[AI] ENTITY {entity.name} id={entity.template_id} pos={entity.position} ai={getattr(entity,'ai_type','?')} beh={getattr(entity,'behavior','')} "
                f"sleepFlags(day={getattr(entity,'sleeps_during_day',False)},night={getattr(entity,'sleeps_during_night',False)}) aware={entity.aware_of_player} move_ctr={entity.move_counter:.2f} hp={entity.hp}/{entity.max_hp} hostile={entity.hostile}"
            )
            # Sleep logic (simple: skip if asleep)
            time_of_day = 'Day' if self.game.fov._is_daytime() else 'Night'
            entity.update_sleep_state(time_of_day)
            if entity.is_sleeping:
                debug(f"[AI]   -> sleeping during {time_of_day}; skipped")
                continue

            # Stealth detection check (only if entity hasn't already spotted player)
            if not entity.has_spotted_player and not entity.aware_of_player:
                ex, ey = entity.position
                dist = math.sqrt((ex - px) ** 2 + (ey - py) ** 2)
                # Only check within reasonable range and with LOS
                if dist <= entity.detection_range and self.game.fov._line_of_sight(ex, ey, px, py):
                    player_stealth = self.game.player.get_stealth_value()
                    entity_perception = entity.get_perception_value()
                    
                    # Light level modifiers
                    light_level = self.game.fov._get_light_level_at(px, py)
                    light_modifier = 0
                    if light_level == 'bright':
                        light_modifier = 5  # Much easier to spot in bright light
                    elif light_level == 'dim':
                        light_modifier = 2  # Somewhat easier in dim light
                    # dark = 0 modifier (no change)
                    
                    # Opposed roll: d20 + perception + light_modifier vs 10 + stealth
                    perception_roll = roll_dice(1, 20) + entity_perception + light_modifier
                    stealth_dc = 10 + player_stealth
                    
                    if perception_roll >= stealth_dc:
                        entity.has_spotted_player = True
                        entity.aware_of_player = True
                        if not entity.hostile and entity.ai_type in ('aggressive', 'pack', 'thief'):
                            entity.hostile = True
                        self.game.log_event(f"{entity.name} spots you!")
                        debug(f"[STEALTH] {entity.name} detected player: roll {perception_roll} (base+light:{entity_perception}+{light_modifier}) vs DC {stealth_dc} (light:{light_level})")
                    else:
                        debug(f"[STEALTH] {entity.name} failed to detect: roll {perception_roll} vs DC {stealth_dc} (light:{light_level})")

            # Tick status effects
            if hasattr(entity, 'status_manager'):
                entity.status_manager.tick_effects()

                # Apply damage-over-time effects to entities
                if hasattr(entity.status_manager, 'get_effect'):
                    poisoned = entity.status_manager.get_effect('Poisoned')
                    if poisoned and poisoned.magnitude > 0:
                        if 'Poisoned' in getattr(entity, 'immunities', []) or 'undead' in getattr(entity, 'tags', []):
                            entity.status_manager.remove_effect('Poisoned')
                        else:
                            poison_dmg = max(1, poisoned.magnitude * poisoned.stacks)
                            entity.take_damage(poison_dmg)
                            if entity.hp <= 0:
                                self.game.log_event(f"{entity.name} succumbs to poison!")
                                # Don't grant XP for poison deaths; stage death for visual removal
                                setattr(entity, '_death_no_xp', True)
                                entity.is_dying = True
                                entity.death_animation_frame = 0
                                continue  # Skip rest of entity processing
                
                    burning = entity.status_manager.get_effect('Burning')
                    if burning and burning.magnitude > 0:
                        # Immunity cleanup (e.g., fire elementals could add 'Burning')
                        if 'Burning' in getattr(entity, 'immunities', []):
                            entity.status_manager.remove_effect('Burning')
                        else:
                            fire_dmg = max(1, burning.magnitude * burning.stacks)
                            # Apply fire resistance if entity has it
                            if hasattr(entity, 'resistances'):
                                fire_resist = entity.resistances.get('fire', 0)
                                multiplier = 1.0 - (fire_resist / 100.0)
                                fire_dmg = max(1, int(fire_dmg * multiplier))
                            entity.take_damage(fire_dmg)
                            if entity.hp <= 0:
                                self.game.log_event(f"{entity.name} is consumed by flames!")
                                # Don't grant XP for burning deaths; stage death for visual removal
                                setattr(entity, '_death_no_xp', True)
                                entity.is_dying = True
                                entity.death_animation_frame = 0
                                continue  # Skip rest of entity processing

            # Dynamic fleeing based on HP, enemy type, and situation
            if entity.hostile and not entity.status_manager.has_behavior('flee'):
                hp_percent = entity.hp / max(1, entity.max_hp)
                
                # Different flee thresholds based on AI type
                ai_type = getattr(entity, 'ai_type', 'passive')
                if ai_type == 'pack':
                    # Pack AI handles its own morale in _pack_entity
                    pass
                elif ai_type == 'thief':
                    # Thieves flee after theft (handled in _thief_entity)
                    pass
                elif ai_type == 'aggressive':
                    # Aggressive enemies flee at lower HP
                    flee_threshold = 0.20
                    if hp_percent < flee_threshold:
                        flee_chance = getattr(entity, 'flee_chance', 40)
                        # Boss-like enemies (high level) less likely to flee
                        level_mod = max(0, 20 - entity.level * 2)
                        flee_chance = max(10, flee_chance - level_mod)
                        
                        if random.randint(1, 100) <= flee_chance:
                            entity.status_manager.add_effect('Fleeing', 8 + random.randint(0, 5))
                            self.game.log_event(f"{entity.name} panics!")
                else:
                    # Default/wander types flee easier
                    flee_threshold = 0.30
                    if hp_percent < flee_threshold:
                        if random.randint(1, 100) <= getattr(entity, 'flee_chance', 50):
                            entity.status_manager.add_effect('Fleeing', 10)
                            self.game.log_event(f"{entity.name} panics!")

            # Movement pacing
            entity.move_counter += 1
            if entity.move_counter < 2:
                debug(f"[AI]   -> move skipped (pacing) move_counter={entity.move_counter:.2f}")
                continue
            entity.move_counter = 0

            # Note: ex, ey, and dist already calculated above for distance culling

            # Maintain awareness for entities that have already spotted player
            if entity.has_spotted_player and dist <= entity.detection_range and self.game.fov._line_of_sight(ex, ey, px, py):
                entity.aware_of_player = True
            elif entity.has_spotted_player and (dist > entity.detection_range or not self.game.fov._line_of_sight(ex, ey, px, py)):
                # Lose awareness if out of range or LOS is broken
                entity.aware_of_player = False
                debug(f"[STEALTH] {entity.name} lost sight of player")

            # Behavior routing
            ai_type = getattr(entity, 'ai_type', 'passive')
            behavior = getattr(entity, 'behavior', '')
            if behavior in ('beggar', 'drunk', 'idiot') and self.game.current_depth == 0:
                debug(f"[AI]   -> town_npc_behavior route: beh={behavior} dist={dist:.2f}")
                self._town_npc_behavior(entity, behavior, dist, px, py)
                continue
            if ai_type == 'passive':
                debug("[AI]   -> passive skip")
                continue
            elif ai_type == 'wander':
                debug(f"[AI]   -> wander route dist={dist:.2f}")
                self._wander_entity(entity)
            elif ai_type == 'aggressive':
                debug(f"[AI]   -> aggressive route dist={dist:.2f} aware={entity.aware_of_player}")
                self._aggressive_entity(entity, dist, px, py)
            elif ai_type == 'pack':
                debug(f"[AI]   -> pack route dist={dist:.2f} aware={entity.aware_of_player}")
                self._pack_entity(entity, dist, px, py)
            elif ai_type == 'thief':
                debug(f"[AI]   -> thief route dist={dist:.2f} aware={entity.aware_of_player}")
                self._thief_entity(entity, dist, px, py)
            else:
                # Default fallback aggressive-like
                if entity.aware_of_player:
                    debug(f"[AI]   -> fallback approach dist={dist:.2f}")
                    self._approach(entity, px, py)
            # Post-action cloning attempt
            self._attempt_entity_clone(entity)
        
        # Performance logging: show lazy AI culling statistics
        if entities_skipped > 0:
            debug(f"[AI] Performance: processed {entities_processed}, skipped {entities_skipped} distant entities")
        
        # Stealth feedback: periodic message if player avoided detection
        self.game._provide_stealth_feedback()
        
        # Process any deaths (drops/xp) after all actions
        self._process_entity_deaths()

    def _compute_xp_reward(self, entity: Entity) -> int:
        """Compute XP reward based on entity stats instead of a flat die roll."""
        lvl = max(1, int(getattr(entity, 'level', 1)))
        hp = max(1, int(getattr(entity, 'max_hp', lvl * 5)))
        atk = max(0, int(getattr(entity, 'attack', 0)))
        df = max(0, int(getattr(entity, 'defense', 0)))
        base = lvl * 8
        score = base + (hp * 0.4) + ((atk + df) * 1.5)

        # Ranged/spell-capable foes are more dangerous
        if getattr(entity, 'ranged_attack', None):
            score *= 1.10
        if getattr(entity, 'spell_list', []):
            score *= 1.15

        # Aggressive AI types push reward upward slightly
        ai_type = getattr(entity, 'ai_type', '').lower()
        if ai_type in ('aggressive', 'pack', 'thief'):
            score *= 1.10

        # Peaceful/neutral creatures give less XP
        if not getattr(entity, 'hostile', False):
            score *= 0.6

        # Depth bonus: modest bump the deeper you are
        try:
            depth = max(0, int(getattr(self.game, 'current_depth', 0)))
            score *= (1.0 + min(0.5, depth / 60.0))
        except Exception:
            pass

        # Clamp to sensible bounds
        score = max(5, min(int(score), 5000))
        return score
    
    def _town_npc_behavior(self, entity: Entity, behavior: str, dist: float, px: int, py: int) -> None:
        """Simple town NPC behaviors: beggar/drunk/idiot interactions."""
        ex, ey = entity.position
        if dist <= 1.5:
            debug(f"[AI][TOWN] {entity.name} interaction range dist={dist:.2f} beh={behavior}")
            if behavior == 'beggar':
                pgold = getattr(self.game.player, 'gold', 0) if self.game.player else 0
                if pgold > 0 and random.random() < 0.6:
                    amt = min(random.randint(1, 5), pgold)
                    if self.game.player:
                        try:
                            self.game.player.gold = max(0, pgold - amt)
                        except Exception:
                            amt = 0
                    self.game.log_event(f"{entity.name} snatches {amt} gold!")
                elif pgold > 0:
                    self.game.log_event(f"{entity.name} pleads.")
                else:
                    self.game.log_event(f"{entity.name} sighs.")
            elif behavior == 'drunk':
                r = random.random()
                if r < 0.4:
                    self.game.log_event(f"{entity.name} urges you to party.")
                elif r < 0.8 and getattr(self.game.player, 'gold', 0) > 0:
                    self.game.log_event(f"{entity.name} asks for ale money.")
                else:
                    self.game.log_event(f"{entity.name} sings.")
            else:  # idiot
                self.game.log_event(f"{entity.name} babbles.")
        else:
            # Drift toward player a bit (beggars/thief-like pursuit is gated)
            if behavior == 'beggar':
                if not self._should_pursue_beggar(dist):
                    debug(f"[AI][TOWN] {entity.name} decides not to pursue (beggar check)")
                    return
            # LOS requirement to move toward the player
            if self.game.fov._line_of_sight(ex, ey, px, py):
                dx = 0 if px == ex else (1 if px > ex else -1)
                dy = 0 if py == ey else (1 if py > ey else -1)
                nx, ny = ex + dx, ey + dy
                if self._is_walkable_for_ai(nx, ny):
                    debug(f"[AI][TOWN] {entity.name} drifts toward player ({ex},{ey})->({nx},{ny})")
                    self._move_entity(entity, nx, ny)
                else:
                    debug(f"[AI][TOWN] {entity.name} drift blocked target=({nx},{ny})")
