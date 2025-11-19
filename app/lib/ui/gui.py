import pygame
from typing import List, Tuple, Dict, Optional

def draw_border(surface: pygame.Surface, gui, rect: pygame.Rect):
    """
    Draws a 9-slice border (corners + tiled edges) around rect.
    Uses sprites from gui.png defined in GUI_MAP.
    """

    def get_sprite(name):
        x, y, w, h = GUI_MAP[name]
        return gui.get(x, y, w, h).convert_alpha()

    tl = get_sprite("border_top_left")
    tr = get_sprite("border_top_right")
    bl = get_sprite("border_bottom_left")
    br = get_sprite("border_bottom_right")
    top = get_sprite("border_top")
    bottom = get_sprite("border_bottom")
    left = get_sprite("border_left")
    right = get_sprite("border_right")

    corner_h = tl.get_height()
    edge_thickness = left.get_width()  # 16px

    # compute edges
    top_y = rect.top - corner_h
    left_x = rect.left - edge_thickness
    right_x = rect.right
    bottom_y = rect.bottom

    # --- tile horizontal edges ---
    w = rect.width
    for x in range(0, w, top.get_width()):
        chunk_w = min(top.get_width(), w - x)
        surface.blit(top.subsurface((0, 0, chunk_w, top.get_height())), (rect.left + x, top_y))
        surface.blit(bottom.subsurface((0, 0, chunk_w, bottom.get_height())), (rect.left + x+5, bottom_y+6))

    # --- tile vertical edges ---
    h = rect.height
    for y in range(0, h, left.get_height()):
        chunk_h = min(left.get_height(), h - y)
        surface.blit(left.subsurface((0, 0, left.get_width(), chunk_h)), (left_x, rect.top + y))
        surface.blit(right.subsurface((0, 0, right.get_width(), chunk_h)), (right_x+6, rect.top + y))

    # --- corners ---
    surface.blit(tl, (left_x, top_y))
    surface.blit(tr, (right_x, top_y))
    surface.blit(bl, (left_x, bottom_y))
    surface.blit(br, (right_x, bottom_y))

def draw_vertical_divider(surface: pygame.Surface, gui, rect: pygame.Rect, x: int):
    """Draw a decorative vertical divider inside an existing bordered frame."""

    def get_sprite(name):
        x0, y0, w, h = GUI_MAP[name]
        return gui.get(x0, y0, w, h).convert_alpha()

    border_left = get_sprite("border_left")
    intersect_top = get_sprite("border_intersect_top")
    intersect_bottom = get_sprite("border_intersect_bottom")

    # Top / bottom intersection pieces
    top_y = rect.top - 25
    bottom_y = rect.bottom - intersect_bottom.get_height() + 25

    surface.blit(intersect_top, (x - intersect_top.get_width() // 2, top_y))
    surface.blit(intersect_bottom, (x - intersect_bottom.get_width() // 2, bottom_y))

    # Vertical tiling between intersections
    inner_top = top_y + intersect_top.get_height()
    inner_bottom = bottom_y
    segment_h = border_left.get_height()

    for y in range(inner_top, inner_bottom, segment_h):
        h = min(segment_h, inner_bottom - y)
        sub = border_left.subsurface((0, 0, border_left.get_width(), h))
        surface.blit(sub, (x - border_left.get_width() // 2, y))



# --- Raw coordinate map ---
GUI_MAP = {
    # --- Wooden Buttons (left column) ---
    "button_normal": (10, 123, 291, 62),
    "button_hover": (10, 201, 291, 62),
    "button_active": (10, 279, 291, 62),
    "button_disabled": (10, 357, 291, 62),

    # --- Checkboxes / Toggles (top-left) ---
    "circle_empty": (13, 9, 33, 32),
    "circle_filled": (13, 45, 33, 32),
    "circle_disabled": (83, 9, 33, 32),

    "arrow_left_normal": (557, 14, 35, 36),
    "arrow_left_hover": (557, 66, 35, 36),
    "arrow_right_normal": (595, 14, 35, 36),
    "arrow_right_hover": (595, 66, 35, 36),
    "arrow_up_normal": (691, 16, 36, 35),
    "arrow_up_hover": (691, 68, 36, 35),
    "arrow_down_normal": (653, 14, 36, 35),
    "arrow_down_hover": (653, 66, 36, 35),

    "field_normal": (10, 123, 291, 62),
    "field_hover": (10, 201, 291, 62),
    "field_active": (10, 279, 291, 62),
    "field_disabled": (10, 357, 291, 62),

    "border_top": (893, 188, 73, 19),
    "border_bottom": (893, 300, 73, 19),
    "border_left": (855, 227, 19, 55),
    "border_right": (984, 227, 19, 55),
    "border_top_left": (855, 188, 25, 25),
    "border_top_right": (978, 188, 25, 25),
    "border_bottom_left": (855, 294, 25, 25),
    "border_bottom_right": (978, 294, 25, 25),
    "border_intersect_top": (775, 166, 31, 25),
    "border_intersect_bottom": (775, 257, 31, 25),
    "border_intersect_left": (781, 208, 25, 31),
    "border_intersect_right": (775, 296, 25, 31),
    "border_intersect": (914, 237, 31, 31),
    "border_end_left": (848, 154, 16, 19),
    "border_end_right": (897, 154, 16, 19),
    "border_end_top": (934, 153, 19, 16),
    "border_end_bottom": (970, 159, 19, 16),
    "divider": (791, 68, 216, 28)
}


# --- Grouped state mappings ---
BUTTON_STATES = {
    "normal": GUI_MAP["button_normal"],
    "hover": GUI_MAP["button_hover"],
    "acvite": GUI_MAP["button_active"],
    "disabled": GUI_MAP["button_disabled"],
}

TOGGLE_STATES = {
    "unchecked": GUI_MAP["circle_empty"],
    "checked": GUI_MAP["circle_filled"],
    "disabled": GUI_MAP["circle_disabled"],
}

ARROW_STATES = {
    "left_normal": GUI_MAP["arrow_left_normal"],
    "left_hover": GUI_MAP["arrow_left_hover"],
    "right_normal": GUI_MAP["arrow_right_normal"],
    "right_hover": GUI_MAP["arrow_right_hover"],
    "up_normal": GUI_MAP["arrow_up_normal"],
    "up_hover": GUI_MAP["arrow_up_hover"],
    "down_normal": GUI_MAP["arrow_down_normal"],
    "down_hover": GUI_MAP["arrow_down_hover"]
}

FIELD_STATES = {
    "normal": GUI_MAP["field_normal"],
    "hover": GUI_MAP["field_hover"],
    "active": GUI_MAP["field_active"],
    "disabled": GUI_MAP["field_disabled"],
}

# --- Helper API ---
def get_region(name: str):
    """Return (x, y, w, h) for a named sprite."""
    return GUI_MAP[name]

def get_button_theme():
    """Return dict of button state rectangles."""
    return BUTTON_STATES.copy()

def get_toggle_theme():
    """Return dict of toggle state rectangles."""
    return TOGGLE_STATES.copy()

def list_all():
    """List all sprite keys."""
    return list(GUI_MAP.keys())


# --------------------------------------------
# Popup and icon helpers used across the UI
# --------------------------------------------
def build_popup(view_rect: pygame.Rect, view_pos: Tuple[int, int], options: List[Tuple[str, str]],
                width: int = 150, btn_h: int = 28, pad: int = 6, style: Optional[Dict] = None) -> Dict:
    """Create a simple popup definition with button rects relative to a view."""
    base_x = max(8, min(view_pos[0], view_rect.width - width - 8))
    total_h = len(options) * (btn_h + pad) - pad
    base_y = max(8, min(view_pos[1], view_rect.height - total_h - 8))
    rects = []
    for idx, (label, action) in enumerate(options):
        rect = pygame.Rect(base_x, base_y + idx * (btn_h + pad), width, btn_h)
        rects.append((rect, action, label))
    return {
        "rects": rects,
        "style": style or {},
    }


def handle_popup_click(popup: Dict, view_pos: Tuple[int, int]) -> Optional[str]:
    """Return the clicked action if any."""
    if not popup:
        return None
    for rect, action, _ in popup.get("rects", []):
        if rect.collidepoint(view_pos):
            return action
    return None


def render_popup(popup: Dict, surface: pygame.Surface, default_bg=(28, 24, 20), default_border=(200, 170, 120)) -> None:
    """Render a generic vertical button popup."""
    if not popup:
        return
    font = pygame.font.Font(None, 20)
    style = popup.get("style", {}) if isinstance(popup, dict) else {}
    bg = style.get("bg", default_bg)
    border = style.get("border", default_border)
    for rect, _, label in popup.get("rects", []):
        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, border, rect, 2, border_radius=4)
        txt = font.render(label, True, (240, 230, 210))
        txt_rect = txt.get_rect(center=rect.center)
        surface.blit(txt, txt_rect)


def render_status_effect_icons(view, surface: pygame.Surface) -> None:
    """Render status effect icons with hover tooltip on a view."""
    game = getattr(view, "game", None)
    if not game:
        return
    player = getattr(game, "player", None)
    if not player or not hasattr(player, "status_manager") or not hasattr(player.status_manager, "get_active_effects"):
        return
    try:
        effects = player.status_manager.get_active_effects()
    except Exception:
        effects = []
    if not effects:
        return

    sprite_manager = getattr(view, "sprite_manager", None)
    if not sprite_manager:
        return

    effect_icon_map = {
        "Poisoned": "cloud_poison_0.png",
        "Burning": "flame_0.png",
        "Blessed": "goldaura_0.png",
        "Cursed": "drain_red_0.png",
        "Weakened": "cloud_gloom_new.png",
        "Silenced": "silenced.png",
    }
    icon_size = 28
    pad = 6
    rect = getattr(view, "rect", None)
    if rect is None:
        return
    x = rect.width - icon_size - pad
    y = int(rect.height * 0.32)
    mouse_pos = pygame.mouse.get_pos()
    local_mouse = (mouse_pos[0] - rect.left, mouse_pos[1] - rect.top)
    hovered = None
    for eff in effects:
        name = getattr(eff, "name", str(eff))
        duration = getattr(eff, "duration", None)
        stacks = getattr(eff, "stacks", 1)
        icon_file = effect_icon_map.get(name, "cloud_magic_trail_0.png")
        icon = sprite_manager.load_sprite(f"images/effect/{icon_file}")
        if icon:
            icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
            surface.blit(icon, (x, y))
            rect_icon = pygame.Rect(x, y, icon_size, icon_size)
            if rect_icon.collidepoint(local_mouse):
                hovered = eff
            overlay_text = None
            if stacks and stacks > 1:
                overlay_text = f"x{stacks}"
            elif duration is not None and duration > 0:
                overlay_text = str(duration)
            if overlay_text:
                font_sm = pygame.font.Font(None, 18)
                txt = font_sm.render(overlay_text, True, (255, 255, 255))
                txt_rect = txt.get_rect(bottomright=(x + icon_size - 2, y + icon_size - 2))
                surface.blit(txt, txt_rect)
        y += icon_size + pad

    if hovered:
        try:
            desc = getattr(hovered, "description", None) or getattr(hovered, "name", "Effect")
            extra = []
            dur_val = getattr(hovered, "duration", None)
            if dur_val:
                extra.append(f"Duration: {dur_val}")
            stacks_val = getattr(hovered, "stacks", 1)
            if stacks_val and stacks_val > 1:
                extra.append(f"Stacks: {stacks_val}")
            lines = [str(desc)] + extra
            font_sm = pygame.font.Font(None, 18)
            padding = 6
            rendered = [font_sm.render(l, True, (230, 230, 230)) for l in lines]
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


# --------------------------------------------
# Trap / tunnel popups
# --------------------------------------------
def build_trap_popup(view_rect: pygame.Rect, view_pos: Tuple[int, int]) -> Dict:
    return build_popup(view_rect, view_pos, [('Disarm', 'disarm'), ('Avoid', 'avoid'), ('Inspect', 'inspect')],
                       width=150, btn_h=28, pad=6, style={'bg': (24, 24, 32), 'border': (180, 160, 100)})


def build_tunnel_popup(view_rect: pygame.Rect, view_pos: Tuple[int, int]) -> Dict:
    return build_popup(view_rect, view_pos, [('Tunnel', 'tunnel'), ('Cancel', 'cancel')],
                       width=150, btn_h=28, pad=6, style={'bg': (28, 24, 20), 'border': (200, 170, 120)})
