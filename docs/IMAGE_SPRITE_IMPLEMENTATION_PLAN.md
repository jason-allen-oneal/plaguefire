# Image Sprite Integration - Implementation Plan

## Overview

This document provides a detailed implementation plan for adding image sprite support to Plaguefire, based on the **Hybrid Textual + Image** approach (Option 1 from the analysis).

---

## Prerequisites

### Decision Points

Before beginning implementation, confirm:
- [ ] Approach chosen: Hybrid (Kitty Protocol), Pygame, or ASCII Enhancement
- [ ] Art style decided: Pixel art size (16x16, 32x32)
- [ ] Asset source confirmed: Custom, OpenGameArt, commissioned, etc.
- [ ] Terminal support requirements: Kitty only, or wider support needed
- [ ] Budget approved for development and assets

### Environment Setup

Required tools and libraries:
```bash
pip install Pillow>=10.0.0
pip install pytest>=7.0.0  # for testing
```

Optional (for development):
```bash
# For sprite sheet creation
pip install aseprite-api  # if using Aseprite
pip install pytiled-parser  # if using Tiled

# For terminal image protocol testing
# Install Kitty terminal: https://sw.kovidgoyal.net/kitty/
```

---

## Phase 1: Research & Prototyping (Week 1)

### Day 1-2: Terminal Image Protocol Investigation

**Goal**: Verify Kitty graphics protocol works with Textual

**Tasks**:
1. Create standalone script to test Kitty graphics protocol
   ```python
   # test_kitty_protocol.py
   import base64
   import sys
   from PIL import Image
   
   def test_kitty_image():
       # Create test image
       img = Image.new('RGB', (32, 32), color='red')
       # ... encode and send via Kitty protocol
   ```

2. Test image display in different terminals:
   - Kitty (primary target)
   - WezTerm (supports Kitty protocol)
   - iTerm2 (different protocol)
   - Standard terminals (should fail gracefully)

3. Measure performance:
   - Image upload time
   - Display latency
   - Update frequency limits

**Deliverable**: `docs/TERMINAL_IMAGE_PROTOCOL_TEST_RESULTS.md`

### Day 3-4: Textual Integration Prototype

**Goal**: Display a single sprite in DungeonView

**Tasks**:
1. Create minimal custom widget:
   ```python
   # app/ui/test_sprite_widget.py
   from textual.widget import Widget
   
   class SpriteTestWidget(Widget):
       def render_sprite(self):
           # Load image with PIL
           # Convert to Kitty protocol
           # Emit to terminal
   ```

2. Test rendering update frequency
3. Test with Textual's reactive system
4. Verify memory usage

**Deliverable**: Working prototype displaying one sprite

### Day 5: Performance Baseline

**Goal**: Establish performance metrics

**Tasks**:
1. Measure current ASCII rendering performance:
   - FPS
   - Memory usage
   - CPU usage
   - Latency

2. Measure prototype sprite rendering:
   - Same metrics
   - Identify bottlenecks

3. Document findings

**Deliverable**: `docs/PERFORMANCE_BASELINE.md`

### Day 6-7: Decision Point

**Review**:
- Does Kitty protocol work adequately?
- Is performance acceptable?
- Are limitations manageable?

**Go/No-Go Decision**:
- ✅ **GO**: Proceed to Phase 2
- ❌ **NO-GO**: Re-evaluate approach or pivot to Option 2 (Pygame)

---

## Phase 2: Architecture Updates (Weeks 2-3)

### Week 2, Day 1-2: Configuration System

**File**: `config.py`

**Changes**:
```python
# Add new configuration constants
RENDER_MODE = "ascii"  # "ascii" or "sprites"
SPRITE_TILE_WIDTH = 16
SPRITE_TILE_HEIGHT = 16
SPRITE_CACHE_SIZE_MB = 50
SPRITE_ANIMATION_ENABLED = True
SPRITE_ATLAS_FORMAT = "packed"  # "packed" or "individual"

# Kitty protocol settings
KITTY_PROTOCOL_ENABLED = True
KITTY_IMAGE_ID_START = 1000
```

**File**: `app/lib/rendering/render_mode.py` (NEW)

```python
from enum import Enum

class RenderMode(Enum):
    """Rendering mode for game display."""
    ASCII = "ascii"
    SPRITES = "sprites"

class TerminalCapability(Enum):
    """Terminal image protocol capabilities."""
    NONE = "none"
    KITTY = "kitty"
    SIXEL = "sixel"
    ITERM2 = "iterm2"
```

**Testing**:
- Verify config loads correctly
- Test enum values
- Ensure backward compatibility

### Week 2, Day 3-5: Sprite Manager

**File**: `app/lib/rendering/sprite_manager.py` (NEW)

**Class Structure**:
```python
class SpriteSheet:
    """Represents a sprite sheet atlas."""
    def __init__(self, path: str, tile_width: int, tile_height: int):
        self.path = path
        self.image = None  # PIL.Image
        self.tile_width = tile_width
        self.tile_height = tile_height
    
    def load(self):
        """Load sprite sheet from disk."""
        pass
    
    def get_sprite(self, x: int, y: int) -> Image:
        """Extract sprite at grid position."""
        pass

class SpriteManager:
    """Manages sprite loading, caching, and lookup."""
    def __init__(self, cache_size_mb: int = 50):
        self.sheets: Dict[str, SpriteSheet] = {}
        self.cache: Dict[str, Image] = {}
        self.cache_size_mb = cache_size_mb
    
    def load_sprite_metadata(self, path: str):
        """Load sprite metadata from JSON."""
        pass
    
    def get_entity_sprite(self, entity_id: str, frame: int = 0) -> Image:
        """Get sprite for entity."""
        pass
    
    def get_item_sprite(self, item_id: str) -> Image:
        """Get sprite for item."""
        pass
    
    def get_terrain_sprite(self, tile_char: str) -> Image:
        """Get sprite for terrain tile."""
        pass
    
    def _cache_sprite(self, key: str, sprite: Image):
        """Add sprite to cache with LRU eviction."""
        pass
```

**Testing**:
- Unit tests for each method
- Memory limit tests
- Cache eviction tests
- Performance benchmarks

### Week 3, Day 1-3: GameData Extensions

**File**: `app/lib/core/loader.py`

**Additions**:
```python
class GameData:
    # ... existing code ...
    
    def load_sprite_metadata(self):
        """Load sprite metadata from data/sprite_metadata.json."""
        metadata = self._load_json("sprite_metadata.json")
        if metadata:
            self.sprite_metadata = metadata
            debug(f"Loaded sprite metadata for {len(metadata)} sheets")
    
    def get_entity_sprite_info(self, entity_id: str) -> Optional[Dict]:
        """Get sprite metadata for entity."""
        entity = self.get_entity(entity_id)
        if entity:
            return entity.get("sprite")
        return None
    
    def get_item_sprite_info(self, item_id: str) -> Optional[Dict]:
        """Get sprite metadata for item."""
        item = self.get_item(item_id)
        if item:
            return item.get("sprite")
        return None
```

**File**: `data/sprite_metadata.json` (NEW)

```json
{
  "sheets": {
    "entities_humanoids": {
      "path": "assets/sprites/entities/humanoids.png",
      "tile_width": 16,
      "tile_height": 16,
      "columns": 16,
      "rows": 16
    },
    "items_potions": {
      "path": "assets/sprites/items/potions.png",
      "tile_width": 16,
      "tile_height": 16,
      "columns": 8,
      "rows": 8
    }
  }
}
```

**Testing**:
- Verify backward compatibility (sprite fields optional)
- Test with missing sprite data
- Ensure fallback to ASCII

### Week 3, Day 4-5: Image Renderer

**File**: `app/lib/rendering/image_renderer.py` (NEW)

**Class Structure**:
```python
class KittyImageRenderer:
    """Render images using Kitty graphics protocol."""
    
    def __init__(self):
        self.capability = self._detect_capability()
        self.next_image_id = KITTY_IMAGE_ID_START
    
    def _detect_capability(self) -> TerminalCapability:
        """Detect terminal image protocol support."""
        # Check environment variables
        # Test protocol handshake
        pass
    
    def render_image(self, image: Image, x: int, y: int, image_id: int = None):
        """Render PIL Image to terminal at position."""
        # Convert image to PNG
        # Encode as base64
        # Send Kitty protocol escape sequence
        pass
    
    def clear_image(self, image_id: int):
        """Remove image from terminal."""
        pass
    
    def composite_viewport(self, tiles: List[List[Image]]) -> Image:
        """Composite tile grid into single viewport image."""
        pass
```

**Testing**:
- Test capability detection
- Test image encoding
- Test protocol communication
- Verify cleanup on exit

---

## Phase 3: Rendering System (Weeks 4-6)

### Week 4, Day 1-3: DungeonView Refactoring

**File**: `app/ui/dungeon_view.py`

**Major Changes**:

1. Add render mode support:
```python
class DungeonView(Static):
    def __init__(self, engine: 'Engine', render_mode: RenderMode = RenderMode.ASCII, **kwargs):
        super().__init__(id="dungeon", **kwargs)
        self.engine = engine
        self.render_mode = render_mode
        self.sprite_manager = None
        self.image_renderer = None
        
        if render_mode == RenderMode.SPRITES:
            self.sprite_manager = SpriteManager()
            self.image_renderer = KittyImageRenderer()
```

2. Split rendering logic:
```python
    def update_map(self):
        """Dispatch to appropriate renderer."""
        if self.render_mode == RenderMode.ASCII:
            self._render_ascii()
        elif self.render_mode == RenderMode.SPRITES:
            self._render_sprites()
    
    def _render_ascii(self):
        """Current implementation - unchanged."""
        # ... existing code ...
    
    def _render_sprites(self):
        """New sprite-based rendering."""
        # Calculate viewport bounds
        # Collect sprites for visible tiles
        # Composite into single image
        # Send to terminal via image_renderer
        pass
```

**Testing**:
- Test mode switching
- Verify ASCII mode still works
- Test sprite mode with minimal sprites

### Week 4, Day 4-5: Sprite Viewport Implementation

**Tasks**:
1. Implement tile → sprite lookup
2. Handle FOV (visible/remembered/unseen)
3. Layer sprites correctly (floor → items → entities → effects)
4. Apply lighting/tinting effects

**Pseudo-code**:
```python
def _render_sprites(self):
    viewport_tiles = self._get_viewport_tiles()
    sprite_grid = []
    
    for row in viewport_tiles:
        sprite_row = []
        for tile_info in row:
            # Get terrain sprite
            terrain_sprite = self.sprite_manager.get_terrain_sprite(tile_info.char)
            
            # Get item sprite if present
            item_sprite = None
            if tile_info.has_item:
                item_sprite = self.sprite_manager.get_item_sprite(tile_info.item_id)
            
            # Get entity sprite if present
            entity_sprite = None
            if tile_info.has_entity:
                entity_sprite = self.sprite_manager.get_entity_sprite(tile_info.entity_id)
            
            # Composite sprites
            composite = self._composite_tile(terrain_sprite, item_sprite, entity_sprite)
            
            # Apply FOV effects
            if tile_info.visibility == 0:
                composite = None  # Hidden
            elif tile_info.visibility == 1:
                composite = self._apply_remembered_effect(composite)
            
            sprite_row.append(composite)
        sprite_grid.append(sprite_row)
    
    # Create final viewport image
    viewport_image = self.image_renderer.composite_viewport(sprite_grid)
    
    # Render to terminal
    self.image_renderer.render_image(viewport_image, 0, 0)
```

### Week 5: Sprite Details

**Day 1-2: Animation System**

```python
class AnimatedSprite:
    def __init__(self, frames: List[Image], frame_duration: float):
        self.frames = frames
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.time_accumulator = 0.0
    
    def update(self, delta_time: float):
        self.time_accumulator += delta_time
        if self.time_accumulator >= self.frame_duration:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.time_accumulator = 0.0
    
    def get_current_frame(self) -> Image:
        return self.frames[self.current_frame]
```

**Day 3: Projectile Rendering**

Adapt existing projectile system to use sprites:
```python
def _render_projectile_sprite(self, projectile):
    pos = projectile.get_current_position()
    sprite = self.sprite_manager.get_projectile_sprite(projectile.type)
    # Render sprite at position
```

**Day 4-5: Effects & Polish**

- Lighting effects (multiply sprite colors)
- Status effect overlays (poison = green tint, etc.)
- Sleeping entities (dim/Zzz icon)
- Damage numbers (text overlay)

### Week 6: Integration & Testing

**Day 1-2: Settings Integration**

**File**: `app/screens/settings.py`

Add graphics mode toggle:
```python
BINDINGS = [
    # ... existing ...
    ("g", "toggle_graphics", "Toggle Graphics Mode"),
]

def action_toggle_graphics(self):
    """Toggle between ASCII and Sprite mode."""
    # Check terminal capability
    if self.app.sprite_mode_available():
        self.app.toggle_graphics_mode()
        self.refresh_display()
    else:
        self.notify("Sprite mode not supported in this terminal", severity="warning")
```

**Day 3-5: Comprehensive Testing**

Test scenarios:
- [ ] Switch modes during gameplay
- [ ] Save/load in different modes
- [ ] Performance under load (100+ entities)
- [ ] Memory usage over time
- [ ] Missing sprites (fallback to ASCII)
- [ ] Terminal without image support
- [ ] Edge cases (invalid images, corrupted data)

---

## Phase 4: Asset Pipeline (Parallel with Phase 3)

### Week 4-6: Asset Creation/Sourcing

**Option A: Use Existing Tileset**

1. Research open-source tilesets:
   - Kenney.nl (CC0 license)
   - OpenGameArt
   - DawnLike tileset
   - Oryx Design Lab (requires purchase)

2. Verify license compatibility
3. Adapt to game's needs
4. Create sprite sheet atlases

**Option B: Commission Custom Art**

1. Define art style guide
2. Create reference sheet
3. Commission artist or hire contractor
4. Iterative review process
5. Final delivery and integration

**Option C: Community/Open Source**

1. Put out call for contributors
2. Provide templates and guidelines
3. Review and integrate submissions
4. Credit artists appropriately

### Asset Organization

```
assets/sprites/
  entities/
    humanoids.png          # 256x256, 16x16 tiles, 16x16 grid
    dragons.png
    undead.png
    animals.png
    ...
  items/
    weapons.png
    armor.png
    potions.png
    scrolls.png
    ...
  terrain/
    dungeon_floor.png
    dungeon_walls.png
    doors.png
    town.png
  effects/
    projectiles.png
    explosions.png
    status_icons.png
```

### Metadata Generation

**File**: `scripts/generate_sprite_metadata.py` (NEW)

```python
#!/usr/bin/env python3
"""Generate sprite metadata from sprite sheets and game data."""

def generate_metadata():
    # Read entities.json
    # Read items.json
    # Scan sprite sheet directories
    # Match entities/items to sprite positions
    # Output sprite_metadata.json
    pass
```

---

## Phase 5: Polish & Optimization (Weeks 7-8)

### Week 7: Performance Optimization

**Day 1-2: Profiling**

Use Python profilers:
```bash
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

Identify bottlenecks:
- Sprite loading
- Image compositing
- Protocol communication
- Memory allocations

**Day 3-4: Optimization**

Implement improvements:
- Lazy loading sprites
- Pre-composite common tile combinations
- Reduce image format conversions
- Optimize cache eviction algorithm

**Day 5: Benchmarking**

Compare before/after:
- FPS improvement
- Memory reduction
- Startup time
- Mode switch time

### Week 8: User Experience

**Day 1-2: Auto-Detection**

```python
def detect_optimal_render_mode() -> RenderMode:
    """Auto-detect best render mode for terminal."""
    capability = detect_terminal_capability()
    
    if capability == TerminalCapability.KITTY:
        return RenderMode.SPRITES
    else:
        return RenderMode.ASCII
```

**Day 3: Error Handling**

- Graceful degradation on errors
- User-friendly error messages
- Fallback mechanisms
- Logging for debugging

**Day 4: Documentation**

Create user documentation:
- How to enable sprite mode
- Terminal requirements
- Troubleshooting guide
- Performance tips

**Day 5: Final Testing**

- User acceptance testing
- Cross-platform verification
- Edge case validation

---

## Rollout Strategy

### Alpha Release (Internal)

- Sprite mode behind feature flag
- Test with core developers
- Gather performance data
- Identify issues

### Beta Release (Limited)

- Enable for opt-in testers
- Community feedback
- Bug fixes
- Performance tuning

### General Release

- Enable by default (with fallback)
- Documentation complete
- Announcement and showcase
- Monitor for issues

---

## Success Metrics

Track these metrics pre/post implementation:

- **Performance**:
  - FPS (target: ≥30 in sprite mode, ≥60 in ASCII)
  - Memory usage (target: ≤100MB increase)
  - Startup time (target: ≤2s additional)

- **Adoption**:
  - % of users with sprite-capable terminals
  - % of users using sprite mode
  - User preference feedback

- **Quality**:
  - Bug count related to rendering
  - User-reported issues
  - Crash rate

- **Maintenance**:
  - Time to add new sprite
  - Code complexity metrics
  - Test coverage

---

## Contingency Plans

### If Performance is Inadequate

1. Reduce sprite resolution (32x32 → 16x16)
2. Limit animation frames
3. Reduce update frequency
4. Implement level-of-detail system

### If Terminal Support is Too Limited

1. Pivot to Option 2 (Pygame window)
2. Create standalone sprite viewer app
3. Focus on ASCII enhancement instead

### If Asset Creation Stalls

1. Use placeholder sprites initially
2. Gradual rollout (common sprites first)
3. Hybrid mode (sprites for some, ASCII for others)

---

## Maintenance Plan

### Ongoing Tasks

- Update sprites when new entities/items added
- Monitor performance over time
- Update for new terminal protocols
- Community sprite contributions

### Documentation

- Keep sprite metadata up to date
- Document sprite creation process
- Maintain artist guidelines
- Version control for assets

---

## Summary Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| 1. Research & Prototype | 1 week | Prototype, performance baseline, go/no-go |
| 2. Architecture | 2 weeks | Config system, sprite manager, data extensions |
| 3. Rendering | 3 weeks | DungeonView updates, sprite rendering, integration |
| 4. Assets | 3 weeks | Sprite sheets, metadata, testing |
| 5. Polish | 2 weeks | Optimization, UX, documentation |
| **Total** | **8-10 weeks** | **Fully functional sprite mode** |

**Note**: Asset creation (Phase 4) runs parallel to Phases 3-5.

---

## Resources Required

### Development
- 1 senior Python developer (full-time, 8-10 weeks)
- OR 2 mid-level developers (part-time, 12-14 weeks)

### Art
- 1 pixel artist (40-80 hours)
- OR Open source tileset license
- OR Community contributions (coordinated)

### Testing
- 2-3 beta testers with various terminals
- Automated test infrastructure

### Tools
- Kitty terminal for development
- Aseprite or similar for sprite editing
- Git LFS for asset version control (optional)

---

## Getting Started

### Immediate Next Steps

1. **Week 0 (Preparation)**:
   - [ ] Read analysis document
   - [ ] Review this implementation plan
   - [ ] Make go/no-go decision
   - [ ] Set up development environment
   - [ ] Install Kitty terminal
   - [ ] Source or create 5-10 test sprites

2. **Week 1 (Research)**:
   - [ ] Follow Phase 1 plan
   - [ ] Build prototype
   - [ ] Measure performance
   - [ ] Document findings
   - [ ] Confirm feasibility

3. **After Week 1**:
   - If GO: Proceed to Phase 2
   - If NO-GO: Re-evaluate or pivot

---

## Questions to Answer During Implementation

- [ ] What's the minimum tile size that looks good?
- [ ] Should we support multiple tile sizes?
- [ ] How do we handle wide/tall entities (dragons, etc.)?
- [ ] Do we need sprite variations (damaged, powered up, etc.)?
- [ ] Should projectiles be animated?
- [ ] How do we indicate sleeping vs awake entities?
- [ ] What about colorblind accessibility?
- [ ] Do we need a sprite editor/viewer tool?

**Recommendation**: Document answers in `docs/SPRITE_DESIGN_DECISIONS.md` as you go.

---

## Conclusion

This implementation plan provides a structured approach to adding sprite support while minimizing risk. The phased approach allows for early validation and course correction if needed.

**Key Success Factors**:
- Early prototyping to validate approach
- Incremental implementation with testing
- Graceful fallbacks for compatibility
- Community engagement for assets
- Performance focus throughout

Good luck with the implementation! 🎮🐉
