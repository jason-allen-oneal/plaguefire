import pygame


def render_traps_and_chests(view, surface: pygame.Surface, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
    """Render trap/chest sprites and tooltip for the provided view."""
    engine = getattr(view, "game", None)
    if not engine or not hasattr(engine, "trap_manager"):
        return
    tile_size = getattr(view, "tile_size", 32)
    trap_manager = engine.trap_manager
    sprite_manager = getattr(view, "sprite_manager", None)
    if not sprite_manager:
        return

    type_variants = {
        "mechanical": ["trap_mechanical.png", "trap_blade.png", "trap_net.png", "pressure_plate.png"],
        "magical": ["trap_magical.png", "trap_teleport.png", "trap_alarm.png"],
        "projectile": ["trap_dart.png", "trap_arrow.png", "trap_needle.png", "trap_spear.png", "trap_axe.png", "trap_bolt.png"],
    }
    mouse_pos = pygame.mouse.get_pos()
    rect = getattr(view, "rect", None)
    if rect is None:
        return
    local_mouse = (mouse_pos[0] - rect.left, mouse_pos[1] - rect.top)
    hovered_grid = None
    if 0 <= local_mouse[0] < rect.width and 0 <= local_mouse[1] < rect.height:
        gx = local_mouse[0] // tile_size + start_x
        gy = local_mouse[1] // tile_size + start_y
        hovered_grid = (gx, gy)
    hovered_trap = None
    for (tx, ty), trap in trap_manager.traps.items():
        if tx < start_x or tx >= end_x or ty < start_y or ty >= end_y:
            continue
        if not trap.get("revealed") and not trap.get("disarmed"):
            continue
        data = trap.get("data", {})
        explicit = data.get("sprite")
        if explicit:
            sprite_candidates = [explicit]
        else:
            ttype = data.get("type") or "mechanical"
            sprite_candidates = type_variants.get(ttype, ["trap_mechanical.png"])
        sprite_name = None
        try:
            key = f"{data.get('id','')}-{tx}-{ty}"
            idx = abs(hash(key)) % len(sprite_candidates)
        except Exception:
            idx = 0

        tried = 0
        spr = None
        total = len(sprite_candidates)
        while tried < total:
            cand = sprite_candidates[(idx + tried) % total]
            spr = sprite_manager.load_sprite(f"images/traps/{cand}", scale_to=(tile_size, tile_size))
            if spr:
                sprite_name = cand
                break
            tried += 1

        if spr:
            sx = (tx - start_x) * tile_size
            sy = (ty - start_y) * tile_size
            surface.blit(spr, (sx, sy))
        if hovered_grid and (tx, ty) == hovered_grid:
            hovered_trap = trap

    for (cx, cy), chest in trap_manager.chests.items():
        if cx < start_x or cx >= end_x or cy < start_y or cy >= end_y:
            continue
        if not chest.get("revealed") and not chest.get("opened"):
            continue
        spr = sprite_manager.load_sprite("images/effect/goldaura_0.png", scale_to=(tile_size, tile_size))
        if spr:
            sx = (cx - start_x) * tile_size
            sy = (cy - start_y) * tile_size
            surface.blit(spr, (sx, sy))

    if hovered_trap:
        try:
            data = hovered_trap.get("data", {})
            name = data.get("name") or data.get("type", "Trap").title()
            diff = data.get("difficulty", "?")
            effect_type = data.get("effect_type") or data.get("trigger", "unknown")
            lines = [name, f"Difficulty: {diff}", f"Effect: {effect_type}"]
            if data.get("status"):
                lines.append(f"Status: {data.get('status')}")
            if data.get("damage"):
                lines.append(f"Damage: {data.get('damage')}")
            try:
                font = engine.assets.font("fonts", "text.ttf", size=14)
            except Exception:
                font = pygame.font.SysFont("Arial", 14)
            padding = 6
            rendered = [font.render(l, True, (230, 230, 230)) for l in lines]
            w = max(r.get_width() for r in rendered) + padding * 2
            h = sum(r.get_height() for r in rendered) + padding * 2
            mx, my = local_mouse
            bx = mx + 12
            by = my + 12
            if bx + w > rect.width:
                bx = rect.width - w - 4
            if by + h > rect.height:
                by = rect.height - h - 4
            box_rect = pygame.Rect(bx, by, w, h)
            pygame.draw.rect(surface, (30, 30, 40), box_rect, border_radius=4)
            pygame.draw.rect(surface, (90, 90, 120), box_rect, 2, border_radius=4)
            cy = by + padding
            for r in rendered:
                surface.blit(r, (bx + padding, cy))
                cy += r.get_height()
        except Exception:
            pass
