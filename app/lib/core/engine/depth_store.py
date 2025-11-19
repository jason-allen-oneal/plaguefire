from typing import Any, Dict

from app.model.entity import Entity


class DepthStore:
    depth_cache: Dict[int, Dict[str, Any]] = {}

    def __init__(self, game):
        self.game = game

        # Initialize depth store attributes
        self.depth_cache = {}

    # ========================
    # Save / Load Game State
    # ========================
    def _serialize_depth_state(self) -> Dict[str, Any]:
        """Serialize state specific to the current depth (map, entities, items, etc.)."""
        if not self.game.current_map:
            return {}
        # Map grid as list of strings for compactness
        map_rows = ["".join(row) for row in self.game.current_map]
        # Entities
        ents = [e.to_dict() for e in self.game.entity_manager.entities]
        # Ground items: serialize keys as "x,y"
        ground = {f"{x},{y}": items[:] for (x, y), items in self.game.ground_items.items()}
        # Traps/chests minimal form: id + state flags + any contents
        traps = {f"{x},{y}": {"id": t.get("id"),
                               "revealed": t.get("revealed", False),
                               "disarmed": t.get("disarmed", False),
                               "single_use": t.get("single_use", True)}
                 for (x, y), t in self.game.trap_manager.traps.items()}
        chests = {f"{x},{y}": {"id": c.get("id"),
                                "opened": c.get("opened", False),
                                "revealed": c.get("revealed", False),
                                "disarmed": c.get("disarmed", False),
                                "contents": list(c.get("contents", []))}
                  for (x, y), c in self.game.trap_manager.chests.items()}
        # Secret door difficulty and known traps
        secret = {f"{x},{y}": diff for (x, y), diff in self.game.secret_door_difficulty.items()}
        known_traps = [f"{x},{y}" for (x, y) in getattr(self, 'known_traps', set())]
        # Visibility is large; persist explored mask only (1/2 treated as explored)
        explored = []
        try:
            for y in range(self.game.map_height):
                row = self.game.fov.visibility[y]
                explored.append([1 if v >= 1 else 0 for v in row])
        except Exception:
            explored = []
        return {
            "map": map_rows,
            "entities": ents,
            "ground_items": ground,
            "death_drop_log": list(self.game.death_drop_log),
            "traps": traps,
            "chests": chests,
            "secret_door_difficulty": secret,
            "known_traps": known_traps,
            "explored": explored,
            "lit_rooms": list(self.game.lit_rooms) if hasattr(self, 'lit_rooms') else [],
        }

    def _deserialize_depth_state(self, data: Dict[str, Any]) -> None:
        """Restore current depth state from serialized data already loaded into Engine.current_depth."""
        if not data:
            return
        # Map
        map_rows = data.get("map", [])
        self.game.current_map = [list(row) for row in map_rows]
        self.game.map_height = len(self.game.current_map) if self.game.current_map else 0
        self.game.map_width = len(self.game.current_map[0]) if self.game.map_height > 0 else 0
        # Rooms cannot be perfectly reconstructed; regenerate simple room list via generator cache where possible
        # Leave self.rooms as-is (may be []); features like lit_rooms still work
        self.visibility = [[0 for _ in range(self.game.map_width)] for _ in range(self.game.map_height)]
        self.light_colors = [[0 for _ in range(self.game.map_width)] for _ in range(self.game.map_height)]
        # Explored mask
        explored = data.get("explored") or []
        if explored and len(explored) == self.game.map_height:
            for y in range(self.game.map_height):
                for x in range(self.game.map_width):
                    try:
                        if explored[y][x]:
                            # mark explored; visible will be updated by update_fov
                            self.visibility[y][x] = 1
                    except Exception:
                        pass
        # Entities
        self.entities = []
        for ed in data.get("entities", []):
            try:
                ent = Entity.from_dict(ed)
                self.entities.append(ent)
            except Exception:
                continue
        # Ground items
        self.ground_items = {}
        for key, items in (data.get("ground_items") or {}).items():
            try:
                x_str, y_str = key.split(",")
                self.ground_items[(int(x_str), int(y_str))] = list(items)
            except Exception:
                continue
        # Death drop log (preserve per-depth drop records)
        try:
            self.death_drop_log = list(data.get("death_drop_log") or [])
        except Exception:
            self.death_drop_log = []
        # Traps
        self.traps = {}
        for key, t in (data.get("traps") or {}).items():
            try:
                x_str, y_str = key.split(",")
                # Rehydrate id via loader
                tdef = self.game.loader.get_trap(t.get("id")) if t.get("id") else None
                self.traps[(int(x_str), int(y_str))] = {
                    'id': t.get('id'),
                    'data': tdef or {},
                    'revealed': bool(t.get('revealed', False)),
                    'disarmed': bool(t.get('disarmed', False)),
                    'single_use': bool(t.get('single_use', True)),
                }
            except Exception:
                continue
        # Chests
        self.chests = {}
        for key, c in (data.get("chests") or {}).items():
            try:
                x_str, y_str = key.split(",")
                cdef = self.game.loader.get_chest(c.get("id")) if hasattr(self.game.loader, 'get_chest') else None
                self.chests[(int(x_str), int(y_str))] = {
                    'id': c.get('id'),
                    'data': cdef or {},
                    'opened': bool(c.get('opened', False)),
                    'revealed': bool(c.get('revealed', False)),
                    'disarmed': bool(c.get('disarmed', False)),
                    'contents': list(c.get('contents', [])),
                }
            except Exception:
                continue
        # Secret doors / known traps / lit rooms
        self.secret_door_difficulty = {}
        for key, diff in (data.get("secret_door_difficulty") or {}).items():
            try:
                x_str, y_str = key.split(",")
                self.secret_door_difficulty[(int(x_str), int(y_str))] = int(diff)
            except Exception:
                continue
        self.known_traps = set()
        for key in data.get("known_traps", []):
            try:
                x_str, y_str = key.split(",")
                self.known_traps.add((int(x_str), int(y_str)))
            except Exception:
                continue
        self.lit_rooms = set(int(i) for i in data.get("lit_rooms", []))

    def save_game(self, path: str) -> Dict[str, Any]:
        """Return a complete save dict and write to path if provided.

        Schema is versioned for future migrations. Returns the save dict.
        """
        # Cache current depth before saving
        if self.game.current_map:
            self.depth_cache[self.current_depth] = self._serialize_depth_state()
        
        # Include data-layer identification mappings so unknown names remain stable
        data_state = {}
        try:
            if hasattr(self.game, 'data') and hasattr(self.game.data, 'to_dict'):
                data_state = self.game.data.to_dict()
        except Exception:
            data_state = {}

        save = {
            "version": 1,
            "time": int(self.time),
            "current_depth": int(self.current_depth),
            "player": self.game.player.to_dict() if getattr(self.game, 'player', None) else {},
            "depth_state": {},
            "data": data_state,
        }
        # Persist all cached depths
        for depth, state in self.depth_cache.items():
            save["depth_state"][str(depth)] = state
        
        # Attempt to write
        try:
            import json, os
            os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(save, indent=2))
        except Exception:
            pass
        return save

    def load_game(self, data: Dict[str, Any]) -> None:
        """Load a save dict created by save_game. Assumes self.game.player already set or will be from data."""
        # Player
        try:
            from app.model.player import Player
            if data.get('player'):
                self.game.player = Player(data['player'], self.game.data)
            self.player = self.game.player
        except Exception:
            pass
        # Core vars
        self.time = int(data.get('time', 0))
        self.current_depth = int(data.get('current_depth', 0))
        
        # Restore all cached depths
        self.depth_cache.clear()
        depth_state_dict = data.get('depth_state') or {}
        for depth_str, state in depth_state_dict.items():
            try:
                depth_int = int(depth_str)
                self.depth_cache[depth_int] = state
            except Exception:
                continue
        
        # Load current depth state
        if self.current_depth in self.depth_cache:
            self._deserialize_depth_state(self.depth_cache[self.current_depth])
        else:
            # Fallback generate a map if not present
            self.game.generate_map(self.current_depth)
        
        # Ensure status manager exists on player
        self.game._ensure_player_status_manager()
        # FOV init
        self.game.fov.update_fov()

        # Restore data-layer identification mappings AFTER base data already loaded
        try:
            data_state = data.get('data') or {}
            if data_state and hasattr(self.game, 'data') and hasattr(self.game.data, 'apply_dict'):
                self.game.data.apply_dict(data_state)
        except Exception:
            pass