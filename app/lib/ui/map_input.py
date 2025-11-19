from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.lib.ui.views.map import MapView


def _calc_tile_from_mouse(view: "MapView", view_mx: int, view_my: int) -> tuple[int, int] | None:
    """Convert view-local mouse coords to map tile coords using the view camera."""
    player = view.game.player
    engine = view.game
    if not player or not player.position or not engine:
        return None
    px, py = player.position
    tiles_wide = view.rect.width // view.tile_size
    tiles_high = view.rect.height // view.tile_size
    start_x = max(0, px - tiles_wide // 2)
    start_y = max(0, py - tiles_high // 2)
    end_x = min(engine.map_width, start_x + tiles_wide + 1)
    end_y = min(engine.map_height, start_y + tiles_high + 1)
    if end_x - start_x < tiles_wide:
        start_x = max(0, end_x - tiles_wide)
    if end_y - start_y < tiles_high:
        start_y = max(0, end_y - tiles_high)
    tile_x = (view_mx // view.tile_size) + start_x
    tile_y = (view_my // view.tile_size) + start_y
    return tile_x, tile_y


def handle_map_click(view: "MapView", event: pygame.event.Event) -> bool:
    """Handle primary map clicks (entities, traps, doors, tunneling, movement)."""
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False

    mx, my = event.pos
    view_mx = mx - view.rect.left
    view_my = my - view.rect.top
    player = view.game.player
    engine = view.game
    if not player or not player.position or not engine:
        return False

    tile_coords = _calc_tile_from_mouse(view, view_mx, view_my)
    if not tile_coords:
        return False
    tile_x, tile_y = tile_coords
    debug = getattr(view, "debug", lambda *args, **kwargs: None)

    # Entity clicks -> info boxes
    clicked_entity = engine.get_entity_at(tile_x, tile_y)
    view_pos = (view_mx, view_my)
    if clicked_entity:
        if clicked_entity is player:
            view.player_info_box.show(player, view_pos)
        else:
            view.info_box.show(clicked_entity, view_pos, player)
        return True
    try:
        if player and player.position and (int(player.position[0]), int(player.position[1])) == (tile_x, tile_y):
            view.player_info_box.show(player, view_pos)
            return True
    except Exception:
        pass

    # Trap popup if revealed
    tm = getattr(engine, "trap_manager", None)
    trap = tm.traps.get((tile_x, tile_y)) if tm and hasattr(tm, "traps") else None
    if trap and (trap.get("revealed") or trap.get("disarmed")):
        view._open_trap_action_popup(trap, (tile_x, tile_y), (view_mx, view_my))
        return True

    # Clear info boxes and paths when clicking open ground
    view.info_box.hide()
    view.player_info_box.hide()
    view._click_move_path = None
    view._trap_action_popup = None
    view._tunnel_action_popup = None

    # Identify clicked tile char
    try:
        cm = getattr(engine, "current_map", None)
        clicked_tile = cm[tile_y][tile_x] if cm and 0 <= tile_y < len(cm) and 0 <= tile_x < len(cm[0]) else None
    except Exception:
        clicked_tile = None

    # Tunnel veins -> open popup
    from config import DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND, QUARTZ_VEIN, MAGMA_VEIN
    if clicked_tile in (QUARTZ_VEIN, MAGMA_VEIN):
        view._open_tunnel_action_popup((tile_x, tile_y), (view_mx, view_my), clicked_tile)
        return True

    # Doors -> path to adjacent and queue open
    if clicked_tile in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND):
        adj, path = view._find_adjacent_path((tile_x, tile_y))
        if path:
            view._click_move_path = path
            view._click_move_door_target = (tile_x, tile_y)
            view._click_move_timer = 0.0
        else:
            if max(abs(player.position[0] - tile_x), abs(player.position[1] - tile_y)) <= 1:
                try:
                    opened = engine.player_open_door(tile_x, tile_y)
                except Exception:
                    opened = False
                if opened:
                    player.position = (tile_x, tile_y)
                    try:
                        engine.fov.update_fov()
                    except Exception:
                        pass
                    if hasattr(engine, "_end_player_turn"):
                        engine._end_player_turn()
                else:
                    blocked = engine.get_entity_at(tile_x, tile_y)
                    if blocked:
                        msg = f"Something is blocking the door: {getattr(blocked, 'name', 'something')}"
                    else:
                        msg = "You can't open the door."
                    if hasattr(view.game, "toasts"):
                        view.game.toasts.show(msg, 2.0, (240, 200, 200), (60, 40, 40))
                    if hasattr(engine, "_end_player_turn"):
                        engine._end_player_turn()
            else:
                if hasattr(view.game, "toasts"):
                    view.game.toasts.show("No path to that door.", 1.8, (220, 220, 200), (60, 40, 30))
        return True

    # Normal click-to-move target
    view._click_move_target = (tile_x, tile_y)
    view._click_move_timer = 0.0
    return True
