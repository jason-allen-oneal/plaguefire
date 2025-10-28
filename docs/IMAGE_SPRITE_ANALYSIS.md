# Image Sprite Integration Analysis

## Executive Summary

This document analyzes the feasibility, difficulty, and process for adding image sprite functionality to Plaguefire, enabling users to switch between ASCII and graphical (image sprite) rendering modes.

**Difficulty Level: Medium to High** (6-8 weeks for full implementation)

**Core Challenge**: Textual framework is designed for terminal-based text rendering, not pixel graphics. Major architectural changes would be required.

---

## Current Architecture Analysis

### Rendering System

#### Current Stack
- **Framework**: Textual 0.77.0 (terminal UI framework)
- **Rendering**: Rich 14.2.0 (terminal formatting)
- **Display**: Character-based (1 character = 1 tile)
- **Output**: ANSI terminal escape sequences
- **Driver**: Custom TruecolorLinuxDriver extending LinuxDriver

#### Key Components
1. **DungeonView** (`app/ui/dungeon_view.py`, 242 lines)
   - Renders viewport using Rich Text markup
   - Character-based tile display
   - FOV-aware rendering
   - Scrolling viewport centered on player
   - Updates via `update_map()` method every 0.01s
   - Projectile animation at 0.05s intervals

2. **GameScreen** (`app/screens/game.py`, 1191 lines)
   - Main game UI container
   - Handles input and game logic
   - Contains DungeonView and HUDView widgets

3. **Engine** (`app/lib/core/engine.py`, 2281 lines)
   - Core game state management
   - Map data as List[List[str]] - character grid
   - Entity/item positioning
   - FOV calculations

### Symbol System

#### Current Implementation
- **Entities**: `char` field in `data/entities.json` (e.g., "D" for dragon, "k" for kobold)
- **Items**: Symbol determined by `_determine_item_symbol()` in `loader.py`
  - Potions: "!"
  - Scrolls/Books: "?"
  - Weapons: "|", "/", "\\"
  - Armor: "[", "(", ")", "]"
  - Wands: "-"
  - Staffs: "_"
  - Gems: "*"
  - Currency: "$"
  - Food: ","
  - Rings: "="
  - Amulets: "\""

- **Terrain**: Defined in `config.py`
  - Wall: "#"
  - Floor: "."
  - Stairs: "<", ">"
  - Doors: "+", "'"
  - Secret doors: "H"
  - Mining veins: "%", "~"

### Color System
- Rich markup tags: `[bright_white]@[/bright_white]`, `[yellow]![/yellow]`
- Entity colors: Direct Rich color names
- Light effects: Yellow tint for lit tiles
- Sleeping entities: Dim effect

---

## Challenges & Constraints

### 1. **Textual Framework Limitations**

**Critical Issue**: Textual is not designed for pixel graphics.

- Textual renders **text characters** to terminal emulators
- No native sprite/image widget
- Rich library doesn't support inline images in terminal output
- Terminal emulators have limited image protocol support (sixel, iTerm2 protocol, kitty protocol)

**Impact**: Would require either:
- Building custom Textual widget for image rendering
- Bypassing Textual entirely for the game view
- Using a different framework for graphical mode

### 2. **Terminal Image Protocol Constraints**

Even with image support, terminal protocols have limitations:

**Sixel Protocol**:
- Limited color palette (256 colors typically)
- Not universally supported
- Performance issues with frequent updates
- No transparency support in most implementations

**Kitty Graphics Protocol**:
- Better performance and features
- Limited terminal support (mainly Kitty terminal)
- Complex implementation

**iTerm2 Inline Images**:
- macOS only
- Not suitable for cross-platform game

### 3. **Rendering Pipeline Changes**

Current: `GameData → Engine → DungeonView (Text) → Rich → Terminal`

Required: `GameData → Engine → Renderer (ASCII or Sprite) → Display`

**Major Changes Needed**:
- Dual rendering paths (ASCII and sprite)
- Image loading and caching system
- Sprite atlas/tileset management
- Pixel-perfect positioning system
- Animation frame management

### 4. **Data Model Extensions**

**Current**: Single character per entity/item/tile

**Required**:
- Sprite sheet references
- Animation frame definitions
- Sprite dimensions (16x16, 32x32, etc.)
- Collision box definitions
- Visual effects metadata

**Example New Structure**:
```json
{
  "id": "ANCIENT_BLACK_DRAGON",
  "name": "Ancient Black Dragon",
  "char": "D",
  "sprite": {
    "sheet": "monsters/dragons.png",
    "index": 15,
    "width": 32,
    "height": 32,
    "frames": 4,
    "animation_speed": 0.2
  }
}
```

### 5. **Asset Creation Requirements**

**Massive Workload**:
- 291 unique entities → 291 sprite designs
- 350 unique items → 350 sprite designs
- Terrain tiles (walls, floors, doors, etc.)
- UI elements and effects
- Multiple animation frames per entity

**Estimated Assets**:
- Minimum: 700+ individual sprites
- With animations: 2000+ frames
- Storage: 5-20 MB (compressed PNG)

### 6. **Performance Considerations**

**ASCII Mode**: ~100 FPS possible, minimal memory
- Simple character grid updates
- Native terminal rendering

**Sprite Mode**:
- Image loading overhead
- Blitting/compositing operations
- Memory for sprite cache (10-50 MB)
- Redraw overhead for viewport
- Target: 30-60 FPS minimum

---

## Proposed Solutions & Approaches

### Option 1: Hybrid Textual + Image (Recommended for Minimal Change)

**Concept**: Keep Textual UI, add optional image overlay

**Approach**:
1. Use terminal image protocol (Kitty graphics preferred)
2. Render sprites via protocol when enabled
3. Fall back to ASCII when unsupported
4. Keep all UI (HUD, menus, text) as Textual widgets

**Pros**:
- Minimal code changes to core game logic
- Maintains Textual architecture
- Automatic fallback for unsupported terminals
- All existing features work

**Cons**:
- Limited terminal support
- Performance constraints
- Complex synchronization between text and image layers
- Image protocol quirks and bugs
- May feel "bolted on"

**Estimated Effort**: 4-6 weeks + asset creation

### Option 2: Pygame/SDL2 Alternative View

**Concept**: Create parallel pygame-based renderer

**Approach**:
1. Add pygame window option (already have pygame for audio)
2. Create `SpriteRenderer` class parallel to `DungeonView`
3. Render game state to pygame surface
4. Keep Textual for menus, character creation, shops
5. Switch to pygame window for dungeon exploration

**Pros**:
- Full control over rendering
- Smooth animations
- Standard sprite/tileset approach
- Better performance
- No terminal limitations

**Cons**:
- Dual UI frameworks (Textual + Pygame)
- Window management complexity
- Breaks "pure terminal" aesthetic
- More complex build/distribution
- Harder to run over SSH/remote

**Estimated Effort**: 6-8 weeks + asset creation

### Option 3: Full Graphical Rewrite (NOT Recommended)

**Concept**: Abandon Textual, use pure pygame/pyglet/arcade

**Pros**:
- Clean architecture for graphics
- Modern game engine features

**Cons**:
- Complete rewrite required
- Lose all Textual advantages
- 3-6 months of work
- Breaks project identity as terminal roguelike

**Estimated Effort**: 12-16 weeks (essentially new game)

### Option 4: Web-Based with Terminal Emulator (Innovative)

**Concept**: Xterm.js + Canvas overlay in web app

**Approach**:
1. Run Textual app in xterm.js terminal emulator
2. Overlay HTML canvas for sprite rendering
3. Synchronize positions between terminal and canvas
4. Deploy as web app or Electron desktop app

**Pros**:
- Cross-platform (runs in browser)
- Best of both worlds
- Share game over web
- Can record/replay easily

**Cons**:
- Complex architecture
- Network/latency considerations
- Requires web server
- Debugging complexity

**Estimated Effort**: 8-12 weeks + asset creation

---

## Recommended Approach: Option 1 (Hybrid)

### Implementation Plan

#### Phase 1: Research & Prototyping (1 week)
1. Test Kitty graphics protocol with Textual
2. Build proof-of-concept image display
3. Measure performance with typical viewport size
4. Validate feasibility on target platforms

#### Phase 2: Architecture Updates (2 weeks)
1. Create `RenderMode` enum (`ASCII`, `SPRITES`)
2. Add mode toggle to settings
3. Create `SpriteManager` class:
   - Load sprite sheets
   - Cache sprites in memory
   - Provide sprite lookup by entity/item ID
4. Extend `GameData`:
   - Add sprite metadata to JSON
   - Backward compatible (sprite fields optional)
5. Create `ImageRenderer` helper:
   - Convert game coordinates to pixel coordinates
   - Handle sprite positioning
   - Manage terminal image protocol

#### Phase 3: Rendering System (2-3 weeks)
1. Modify `DungeonView`:
   - Add `render_mode` parameter
   - Implement `_render_ascii()` (current behavior)
   - Implement `_render_sprites()` (new)
   - Smart switching based on mode
2. Implement sprite viewport:
   - Calculate visible tiles
   - Load required sprites
   - Composite into single image
   - Send via terminal protocol
3. Handle FOV with sprites (dimming/hiding)
4. Projectile animations with sprites

#### Phase 4: Asset Pipeline (Parallel with Phase 3)
1. Choose tile size (16x16 or 32x32 recommended)
2. Create sprite sheet template
3. Design/commission sprites:
   - Priority: Player, common monsters, terrain
   - Then: Items, special entities
   - Last: Rare monsters, special effects
4. Create sprite sheet atlas
5. Generate metadata JSON

#### Phase 5: Polish & Optimization (1-2 weeks)
1. Performance profiling
2. Sprite caching optimization
3. Smooth scrolling with sprites
4. Animation system
5. Fallback detection and UI messaging

---

## Technical Requirements

### New Dependencies

```python
# requirements.txt additions
Pillow>=10.0.0        # Image loading and manipulation
```

### New Files

```
app/
  lib/
    rendering/
      __init__.py
      sprite_manager.py     # Sprite loading and caching
      image_renderer.py     # Terminal image protocol
      render_mode.py        # RenderMode enum
  ui/
    sprite_view.py          # Alternative to DungeonView for sprites
assets/
  sprites/
    entities/
      dragons.png
      humanoids.png
      undead.png
      ...
    items/
      weapons.png
      armor.png
      potions.png
      ...
    terrain/
      dungeon.png
      town.png
    effects/
      projectiles.png
      animations.png
data/
  sprite_metadata.json    # Sprite sheet definitions
```

### Data Schema Extensions

**entities.json**:
```json
{
  "id": "KOBOLD",
  "name": "Kobold",
  "char": "k",
  "sprite": {
    "sheet": "entities/humanoids.png",
    "x": 0,
    "y": 32,
    "width": 16,
    "height": 16,
    "frames": 1
  }
}
```

**items.json**:
```json
{
  "POTION_HEALING": {
    "name": "Potion of Healing",
    "type": "potion",
    "sprite": {
      "sheet": "items/potions.png",
      "x": 0,
      "y": 0,
      "width": 16,
      "height": 16
    }
  }
}
```

### Configuration Updates

**config.py**:
```python
# Rendering configuration
RENDER_MODE = "ascii"  # "ascii" or "sprites"
SPRITE_TILE_WIDTH = 16
SPRITE_TILE_HEIGHT = 16
SPRITE_CACHE_SIZE_MB = 50
USE_SPRITE_ANIMATIONS = True
```

**Settings UI Addition**:
- Toggle: `[G]raphics Mode: ASCII / Sprites`
- Auto-detect terminal capability
- Show warning if terminal doesn't support images

---

## Risk Assessment

### High Risk Issues

1. **Terminal Compatibility** (Severity: High)
   - Many terminals don't support image protocols
   - Mitigation: Graceful fallback, clear messaging

2. **Performance** (Severity: Medium)
   - Image updates may lag on older hardware
   - Mitigation: Optimize caching, reduce update frequency, offer quality settings

3. **Asset Quality** (Severity: Medium)
   - Inconsistent art style may harm experience
   - Mitigation: Use established tileset or commission professional art

4. **Scope Creep** (Severity: High)
   - Feature may expand to animations, effects, etc.
   - Mitigation: Strict phase gating, MVP definition

### Medium Risk Issues

1. **Maintenance Burden**
   - Dual rendering paths = 2x testing
   - Mitigation: Shared game logic, thorough unit tests

2. **User Confusion**
   - Users may not understand why sprites don't work
   - Mitigation: Detection, auto-configure, helpful errors

3. **Save Compatibility**
   - Ensure saves work regardless of render mode
   - Mitigation: Render mode not stored in saves

---

## Alternative: ASCII Art Enhancement

### Lower-Effort Alternative

Instead of full sprite support, enhance ASCII mode:

1. **Unicode Box Drawing** - Better walls/borders
2. **Extended ASCII Art** - Multi-char monsters (2x2, 3x3)
3. **Better Color Palette** - Richer colors for entities
4. **Dithering Effects** - ASCII art backgrounds
5. **Animation Frames** - Alternate characters for animation

**Pros**:
- No protocol dependencies
- Works in all terminals
- Stays true to roguelike roots
- Much faster to implement (2-3 weeks)

**Cons**:
- Still text-based
- Limited visual fidelity
- Not "true" sprites

---

## Conclusion

### Recommended Path Forward

1. **Short-term** (Now):
   - Implement ASCII art enhancements (Unicode, better colors)
   - Add animation frames for ASCII
   - Polish existing rendering

2. **Medium-term** (3-6 months):
   - Prototype Kitty graphics protocol integration
   - Create minimal sprite set (player, 10 monsters, basic items)
   - Test with community for feedback

3. **Long-term** (6-12 months):
   - If prototype successful, full sprite system
   - Commission or source complete tileset
   - Full implementation per Phase plan

### Success Criteria

- [ ] Sprite mode works in at least Kitty terminal
- [ ] Automatic fallback to ASCII in unsupported terminals
- [ ] No performance regression in ASCII mode
- [ ] 60+ FPS in sprite mode on modern hardware
- [ ] Save files work in both modes
- [ ] Complete sprite coverage (all entities/items/tiles)
- [ ] Player can toggle modes seamlessly
- [ ] Documentation for artists to add sprites

### Effort Summary

**Minimum Viable Product**:
- Development: 4-6 weeks (1 developer)
- Art/Assets: 40-80 hours (depending on style)
- Testing: 1-2 weeks
- **Total**: 8-10 weeks

**Full Implementation**:
- Development: 8-12 weeks
- Art/Assets: 120-200 hours
- Testing: 2-3 weeks
- Polish: 1-2 weeks
- **Total**: 14-18 weeks

### Budget Considerations

- **Developer Time**: 200-400 hours @ $50-150/hr = $10,000-60,000
- **Artist Time**: 120-200 hours @ $25-100/hr = $3,000-20,000
- **Testing/QA**: 80-120 hours @ $30-80/hr = $2,400-9,600
- **Total Estimated Cost**: $15,400-89,600 (wide range based on quality/scope)

**Open Source Alternative**:
- Use existing tilesets (e.g., Kenney.nl, OpenGameArt)
- Community contributions
- Estimated cost: $0-5,000 (just development time)

---

## Next Steps

If proceeding with this feature:

1. **Decision**: Choose approach (Hybrid, Pygame, or Enhanced ASCII)
2. **Prototype**: Build proof-of-concept (1 week)
3. **Art Style**: Define visual direction, find tileset
4. **Community Input**: Share prototype, gather feedback
5. **Commitment**: Only proceed if prototype validates approach
6. **Implementation**: Follow phased plan above

**Recommendation**: Start with ASCII art enhancements to improve visual appeal with minimal risk, then evaluate sprite mode if there's strong demand and resources available.
