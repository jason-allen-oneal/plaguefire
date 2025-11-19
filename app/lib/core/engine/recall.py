from typing import Dict, Optional, Tuple


class RecallManager:
    def __init__(self, game):
        self.game = game

         # Recall spell
        self.recall_active = False
        self.recall_timer = 0
        self.recall_turns = 20
        # Default cooldown (in turns) applied when using recall (scroll or spell fallback)
        self.recall_cooldown_turns = 200
        self.recall_target_depth: Optional[int] = None
        self.recall_target_pos: Optional[Tuple[int, int]] = None
    
    # -------------------------
    # Recall Spell
    # -------------------------
    def activate_recall(self):
        # Backwards-compatible: simple recall with no anchor name
        self.activate_recall_to_anchor(None)

    def activate_recall_to_anchor(self, anchor_name: Optional[str] = None):
        """Begin a delayed recall. If anchor_name is provided, recall to that anchor if present on player.

        This method is the generalized entrypoint; older callers can still call activate_recall().
        """
        if self.recall_active:
            self.game.log_event('You are already recalling!')
            return
        # Enforce recall cooldown on player (prevents repeated use)
        try:
            if self.game.player and hasattr(self.game.player, 'is_spell_on_cooldown') and self.game.player.is_spell_on_cooldown('recall'):
                self.game.log_event('You cannot recall yet.')
                return
        except Exception:
            pass
        target = None
        self.recall_target_pos = None
        if anchor_name and self.game.player:
            anchors = getattr(self.game.player, 'recall_anchors', {}) or {}
            anchor = anchors.get(anchor_name)
            if not anchor:
                self.game.log_event('No such recall anchor.')
                return
            target = int(anchor.get('depth', 0))
            pos = anchor.get('pos')
            if pos:
                try:
                    self.recall_target_pos = (int(pos[0]), int(pos[1]))
                except Exception:
                    self.recall_target_pos = None
        else:
            # Default behavior: recall to town (depth 0) if in dungeon, otherwise to deepest known depth
            target = 0 if self.game.current_depth > 0 else getattr(self.game.player, 'deepest_depth', 1)

        if target is None or target == self.game.current_depth:
            self.game.log_event('You have nowhere to recall to.')
            return

        self.recall_target_depth = int(target)
        self.recall_active = True
        self.recall_timer = 0
        # Apply cooldown to player for recall usage
        try:
            if self.game.player and hasattr(self.game.player, 'set_spell_cooldown'):
                self.game.player.set_spell_cooldown('recall', int(self.recall_cooldown_turns))
        except Exception:
            pass
        self.game.log_event('You begin to recall...')

    def _execute_recall(self):
        if not self.recall_active or self.recall_target_depth is None:
            return
        self.game.log_event('The world blurs...')
        # Move to the target depth then attempt to place at a remembered anchor pos (if any)
        target_depth = int(self.recall_target_depth)
        self.game.change_depth(target_depth)
        # If an anchor position was requested, place the player there (best-effort)
        if self.recall_target_pos and self.game.player and hasattr(self.game.player, 'position'):
            try:
                self.game.player.position = [int(self.recall_target_pos[0]), int(self.recall_target_pos[1])]
                from app.lib.utils import ensure_valid_player_position
                ensure_valid_player_position(self, self.game.player)
                self.game.log_event('You arrive at your anchor.')
            except Exception:
                pass
        self.recall_active = False
        self.recall_timer = 0
        self.recall_target_depth = None
        self.recall_target_pos = None

    # -------------------------
    # Recall anchor management helpers (UI-facing)
    # -------------------------
    def get_player_recall_anchors(self) -> Dict[str, Dict]:
        """Return the player's recall anchors dict (name -> {depth,pos})."""
        if not self.game.player:
            return {}
        return getattr(self.game.player, 'recall_anchors', {}) or {}

    def bind_player_anchor(self, name: str) -> None:
        """Bind the player's current position/depth to an anchor name."""
        if not self.game.player:
            return
        try:
            pos = getattr(self.game.player, 'position', [0, 0])
            self.game.player.bind_recall_anchor(name, int(self.game.current_depth), pos)
            self.game.log_event(f"Anchor '{name}' bound to depth {self.game.current_depth}.")
        except Exception:
            self.game.log_event('Failed to bind anchor.')

    def remove_player_recall_anchor(self, name: str) -> bool:
        """Remove a named anchor from the player. Returns True if removed."""
        if not self.game.player:
            return False
        try:
            removed = self.game.player.remove_recall_anchor(name)
            if removed:
                self.game.log_event(f"Anchor '{name}' removed.")
            return removed
        except Exception:
            return False