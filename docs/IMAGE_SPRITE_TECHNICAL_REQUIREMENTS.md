# Image Sprite Integration - Technical Requirements

## Document Purpose

This document specifies the technical requirements, API contracts, and system interfaces needed to implement image sprite support in Plaguefire.

---

## System Requirements

### Software Requirements

#### Development Environment
- Python 3.8+ (tested on 3.13.7)
- pip package manager
- Git + Git LFS (optional, for large sprite sheets)
- Kitty terminal 0.26.0+ (for development/testing)

#### Runtime Requirements

**Required**:
- Python 3.8+
- textual==0.77.0
- rich==14.2.0
- pygame==2.6.1
- Pillow>=10.0.0 (NEW)

**Optional**:
- Terminal with image protocol support (Kitty, WezTerm, iTerm2)

### Hardware Requirements

#### Minimum
- CPU: Dual-core 1.5 GHz
- RAM: 512 MB available
- Storage: 50 MB for sprite assets
- Display: 80x24 terminal, 256 colors

#### Recommended
- CPU: Quad-core 2.0 GHz+
- RAM: 1 GB available
- Storage: 100 MB for sprite assets
- Display: 120x40 terminal, truecolor support

---

## Feature Requirements

### FR-1: Dual Rendering Mode

**Priority**: P0 (Must Have)

**Description**: System shall support both ASCII and sprite rendering modes.

**Acceptance Criteria**:
- [ ] User can select ASCII or Sprite mode in settings
- [ ] Mode can be changed during gameplay
- [ ] Mode preference is persisted across sessions
- [ ] Game state is independent of rendering mode
- [ ] Save files work in both modes

**Technical Details**:
```python
class RenderMode(Enum):
    ASCII = "ascii"
    SPRITES = "sprites"

# Configuration
RENDER_MODE: RenderMode = RenderMode.ASCII
```

### FR-2: Terminal Capability Detection

**Priority**: P0 (Must Have)

**Description**: System shall automatically detect terminal image protocol support.

**Acceptance Criteria**:
- [ ] Detects Kitty graphics protocol support
- [ ] Detects Sixel protocol support (future)
- [ ] Detects iTerm2 protocol support (future)
- [ ] Falls back gracefully to ASCII if unsupported
- [ ] Displays user-friendly message about capabilities

**Technical Details**:
```python
def detect_terminal_capability() -> TerminalCapability:
    """
    Detect terminal image protocol support.
    
    Returns:
        TerminalCapability enum indicating support level
    """
    # Check environment variables
    term = os.environ.get('TERM', '')
    term_program = os.environ.get('TERM_PROGRAM', '')
    
    # Check for Kitty
    if 'kitty' in term or term_program == 'kitty':
        return TerminalCapability.KITTY
    
    # Check for iTerm2
    if term_program == 'iTerm.app':
        return TerminalCapability.ITERM2
    
    # Check for sixel support via terminfo
    # ... implementation ...
    
    return TerminalCapability.NONE
```

### FR-3: Sprite Loading and Management

**Priority**: P0 (Must Have)

**Description**: System shall efficiently load and cache sprite data.

**Acceptance Criteria**:
- [ ] Loads sprite sheets from PNG files
- [ ] Caches sprites in memory with configurable limit
- [ ] Implements LRU eviction when cache is full
- [ ] Supports lazy loading (load on first use)
- [ ] Handles missing sprites gracefully (fallback to ASCII)
- [ ] Reports sprite loading errors clearly

**Technical Details**:
```python
class SpriteManager:
    def __init__(self, cache_size_mb: int = 50):
        self.cache_size_mb = cache_size_mb
        self.cache: OrderedDict[str, Image] = OrderedDict()
        self.current_cache_size = 0
    
    def get_sprite(self, key: str) -> Optional[Image]:
        """
        Get sprite from cache or load from disk.
        
        Args:
            key: Sprite identifier (e.g., "entity:KOBOLD:0")
        
        Returns:
            PIL Image or None if not found
        """
        pass
    
    def _evict_lru(self):
        """Evict least recently used sprites to free memory."""
        pass
```

### FR-4: Viewport Compositing

**Priority**: P0 (Must Have)

**Description**: System shall composite viewport from individual tile sprites.

**Acceptance Criteria**:
- [ ] Combines terrain, items, and entity sprites
- [ ] Respects z-order (floor < items < entities < effects)
- [ ] Applies FOV effects (visible/remembered/hidden)
- [ ] Handles transparency correctly
- [ ] Renders to viewport dimensions
- [ ] Updates at minimum 30 FPS

**Technical Details**:
```python
def composite_viewport(self, tiles: List[List[TileInfo]]) -> Image:
    """
    Create composite image from tile grid.
    
    Args:
        tiles: 2D array of TileInfo objects
    
    Returns:
        Composite PIL Image of entire viewport
    """
    viewport_width = len(tiles[0]) * SPRITE_TILE_WIDTH
    viewport_height = len(tiles) * SPRITE_TILE_HEIGHT
    
    composite = Image.new('RGBA', (viewport_width, viewport_height))
    
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            # Get and composite sprites
            # ... implementation ...
    
    return composite
```

### FR-5: Animation Support

**Priority**: P1 (Should Have)

**Description**: System shall support animated sprites with multiple frames.

**Acceptance Criteria**:
- [ ] Loads multi-frame sprites from sprite sheets
- [ ] Cycles through frames based on configured speed
- [ ] Synchronizes animation timing
- [ ] Supports per-entity animation states (idle, walking, attacking)
- [ ] Can disable animations for performance

**Technical Details**:
```python
class AnimatedSprite:
    def __init__(self, frames: List[Image], fps: float = 10.0):
        self.frames = frames
        self.fps = fps
        self.frame_duration = 1.0 / fps
        self.current_frame = 0
        self.elapsed = 0.0
    
    def update(self, delta_time: float) -> bool:
        """
        Update animation state.
        
        Returns:
            True if frame changed
        """
        self.elapsed += delta_time
        if self.elapsed >= self.frame_duration:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.elapsed = 0.0
            return True
        return False
```

### FR-6: Image Protocol Communication

**Priority**: P0 (Must Have)

**Description**: System shall communicate with terminal using appropriate image protocol.

**Acceptance Criteria**:
- [ ] Implements Kitty graphics protocol
- [ ] Encodes images correctly (PNG + base64)
- [ ] Sends escape sequences properly
- [ ] Handles image IDs and placement
- [ ] Cleans up images when no longer needed
- [ ] Handles protocol errors gracefully

**Technical Details**:
```python
class KittyImageRenderer:
    def render_image(self, image: Image, x: int, y: int, image_id: int) -> bool:
        """
        Render image to terminal using Kitty graphics protocol.
        
        Args:
            image: PIL Image to display
            x, y: Terminal character coordinates
            image_id: Unique ID for this image
        
        Returns:
            True if successful, False otherwise
        """
        # Convert image to PNG
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        png_data = buffer.getvalue()
        
        # Encode as base64
        b64_data = base64.standard_b64encode(png_data).decode('ascii')
        
        # Build Kitty escape sequence
        chunks = [b64_data[i:i+4096] for i in range(0, len(b64_data), 4096)]
        
        for i, chunk in enumerate(chunks):
            m = 1 if i < len(chunks) - 1 else 0
            escape_seq = f"\x1b_Gf=100,i={image_id},m={m};{chunk}\x1b\\"
            sys.stdout.write(escape_seq)
        
        sys.stdout.flush()
        return True
```

### FR-7: Fallback Mechanism

**Priority**: P0 (Must Have)

**Description**: System shall gracefully fall back to ASCII when sprites unavailable.

**Acceptance Criteria**:
- [ ] Missing sprite → use ASCII character
- [ ] Unsupported terminal → auto-switch to ASCII mode
- [ ] Failed sprite load → log warning, use fallback
- [ ] User can force ASCII mode regardless of support
- [ ] Fallback is transparent to game logic

### FR-8: Data Schema Extensions

**Priority**: P0 (Must Have)

**Description**: Entity and item data shall support optional sprite metadata.

**Acceptance Criteria**:
- [ ] entities.json supports optional "sprite" field
- [ ] items.json supports optional "sprite" field
- [ ] Existing data remains valid (backward compatible)
- [ ] Sprite metadata is validated on load
- [ ] Missing sprite metadata handled gracefully

**Schema**:
```json
{
  "sprite": {
    "sheet": "entities/humanoids.png",
    "x": 0,
    "y": 32,
    "width": 16,
    "height": 16,
    "frames": 1,
    "animation_fps": 10.0
  }
}
```

### FR-9: Performance Monitoring

**Priority**: P1 (Should Have)

**Description**: System shall provide performance metrics for sprite rendering.

**Acceptance Criteria**:
- [ ] Tracks FPS for both rendering modes
- [ ] Monitors memory usage
- [ ] Reports cache hit/miss rates
- [ ] Logs performance warnings
- [ ] Provides debug overlay (optional)

**Technical Details**:
```python
class PerformanceMonitor:
    def __init__(self):
        self.frame_times: deque = deque(maxlen=60)
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_frame(self, duration: float):
        self.frame_times.append(duration)
    
    def get_fps(self) -> float:
        if not self.frame_times:
            return 0.0
        avg_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_time if avg_time > 0 else 0.0
    
    def get_cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
```

### FR-10: Settings Integration

**Priority**: P0 (Must Have)

**Description**: Settings screen shall provide graphics mode toggle.

**Acceptance Criteria**:
- [ ] Settings screen has "Graphics Mode" option
- [ ] Shows current mode (ASCII / Sprites)
- [ ] Indicates if sprite mode is available
- [ ] Changes take effect immediately
- [ ] Preference is saved to config

---

## Non-Functional Requirements

### NFR-1: Performance

**Target Metrics**:
- ASCII Mode: ≥60 FPS
- Sprite Mode: ≥30 FPS
- Mode Switch: <1 second
- Memory Overhead: <100 MB for sprite cache
- Startup Time Increase: <2 seconds

**Measurement**:
```python
# Performance test script
def test_rendering_performance():
    # Render 1000 frames
    # Measure time, FPS, memory
    assert avg_fps >= 30
    assert max_memory_mb <= 100
```

### NFR-2: Compatibility

**Supported Terminals**:
- Kitty terminal (primary)
- WezTerm (Kitty protocol support)
- Any terminal (ASCII fallback)

**Supported Platforms**:
- Linux (primary)
- macOS (secondary)
- Windows (via WSL, tertiary)

### NFR-3: Reliability

**Error Handling**:
- All sprite operations must handle failures gracefully
- No crashes due to missing/corrupt sprites
- Clear error messages for users
- Detailed logs for debugging

**Availability**:
- Game playable in ASCII mode even if sprite mode fails
- No degradation of ASCII mode performance

### NFR-4: Maintainability

**Code Quality**:
- Type hints for all public APIs
- Docstrings for all classes and methods
- Unit tests for all sprite management code
- Integration tests for rendering pipeline

**Documentation**:
- API documentation for sprite system
- User guide for sprite mode
- Artist guide for creating sprites
- Troubleshooting guide

### NFR-5: Scalability

**Asset Management**:
- Support 500+ unique sprites
- Support sprite sheets up to 4096x4096
- Handle 100+ on-screen sprites simultaneously

**Memory Management**:
- Configurable cache size
- Automatic eviction of unused sprites
- Lazy loading of sprite sheets

---

## API Specifications

### SpriteManager API

```python
class SpriteManager:
    """Manages sprite loading, caching, and retrieval."""
    
    def __init__(self, cache_size_mb: int = 50, lazy_load: bool = True):
        """
        Initialize sprite manager.
        
        Args:
            cache_size_mb: Maximum memory for sprite cache
            lazy_load: Load sprites on-demand vs all at startup
        """
        pass
    
    def load_metadata(self, metadata_path: str) -> bool:
        """
        Load sprite metadata from JSON file.
        
        Args:
            metadata_path: Path to sprite_metadata.json
        
        Returns:
            True if successful
        
        Raises:
            FileNotFoundError: If metadata file missing
            JSONDecodeError: If metadata invalid
        """
        pass
    
    def get_entity_sprite(self, entity_id: str, frame: int = 0) -> Optional[Image]:
        """
        Get sprite for entity.
        
        Args:
            entity_id: Entity template ID (e.g., "KOBOLD")
            frame: Animation frame index
        
        Returns:
            PIL Image or None if not found
        """
        pass
    
    def get_item_sprite(self, item_id: str) -> Optional[Image]:
        """
        Get sprite for item.
        
        Args:
            item_id: Item template ID
        
        Returns:
            PIL Image or None if not found
        """
        pass
    
    def get_terrain_sprite(self, tile_char: str, variant: int = 0) -> Optional[Image]:
        """
        Get sprite for terrain tile.
        
        Args:
            tile_char: Terrain character ('#', '.', etc.)
            variant: Variant index for tiles with multiple sprites
        
        Returns:
            PIL Image or None if not found
        """
        pass
    
    def preload_common_sprites(self, entity_ids: List[str], item_ids: List[str]):
        """
        Preload frequently used sprites into cache.
        
        Args:
            entity_ids: Entity IDs to preload
            item_ids: Item IDs to preload
        """
        pass
    
    def clear_cache(self):
        """Clear all cached sprites to free memory."""
        pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with keys: size_mb, hit_rate, entries
        """
        pass
```

### ImageRenderer API

```python
class KittyImageRenderer:
    """Renders images using Kitty graphics protocol."""
    
    def __init__(self):
        """Initialize renderer and detect capabilities."""
        pass
    
    def is_supported(self) -> bool:
        """
        Check if Kitty protocol is supported.
        
        Returns:
            True if terminal supports Kitty graphics
        """
        pass
    
    def render_image(self, image: Image, x: int, y: int, image_id: int) -> bool:
        """
        Render image to terminal.
        
        Args:
            image: PIL Image to display
            x: Column position (in characters)
            y: Row position (in characters)
            image_id: Unique identifier for this image
        
        Returns:
            True if successful
        
        Raises:
            ProtocolError: If terminal communication fails
        """
        pass
    
    def clear_image(self, image_id: int):
        """
        Remove image from display.
        
        Args:
            image_id: ID of image to remove
        """
        pass
    
    def clear_all_images(self):
        """Remove all rendered images."""
        pass
    
    def composite_viewport(self, 
                          sprites: List[List[Optional[Image]]],
                          tile_width: int,
                          tile_height: int) -> Image:
        """
        Composite sprite grid into single image.
        
        Args:
            sprites: 2D array of sprite Images (None for empty)
            tile_width: Width of each tile in pixels
            tile_height: Height of each tile in pixels
        
        Returns:
            Composite viewport image
        """
        pass
```

### DungeonView API Changes

```python
class DungeonView(Static):
    """Renders game map with ASCII or sprite mode."""
    
    def __init__(self, 
                 engine: 'Engine',
                 render_mode: RenderMode = RenderMode.ASCII,
                 **kwargs):
        """
        Initialize dungeon view.
        
        Args:
            engine: Game engine instance
            render_mode: Rendering mode (ASCII or SPRITES)
            **kwargs: Additional widget arguments
        """
        pass
    
    def set_render_mode(self, mode: RenderMode):
        """
        Change rendering mode.
        
        Args:
            mode: New rendering mode
        """
        pass
    
    def update_map(self):
        """Refresh map display using current render mode."""
        pass
```

---

## Data Specifications

### Sprite Metadata Format

**File**: `data/sprite_metadata.json`

```json
{
  "version": "1.0",
  "tile_width": 16,
  "tile_height": 16,
  "sheets": {
    "entities_humanoids": {
      "path": "assets/sprites/entities/humanoids.png",
      "columns": 16,
      "rows": 16,
      "tile_width": 16,
      "tile_height": 16
    }
  },
  "entities": {
    "KOBOLD": {
      "sheet": "entities_humanoids",
      "x": 0,
      "y": 0,
      "frames": 1
    },
    "GOBLIN": {
      "sheet": "entities_humanoids",
      "x": 16,
      "y": 0,
      "frames": 2,
      "animation_fps": 8.0
    }
  },
  "items": {
    "POTION_HEALING": {
      "sheet": "items_potions",
      "x": 0,
      "y": 0
    }
  },
  "terrain": {
    "#": {
      "sheet": "terrain_dungeon",
      "x": 0,
      "y": 0,
      "variants": 4
    },
    ".": {
      "sheet": "terrain_dungeon",
      "x": 64,
      "y": 0
    }
  }
}
```

### Entity Data Extension

**File**: `data/entities.json`

Add optional `sprite` field:

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
    "frames": 2,
    "animation_fps": 10.0
  },
  "hp_base": 10,
  "...": "..."
}
```

**Validation Rules**:
- `sprite` field is optional
- If present, must have at minimum: `sheet`, `x`, `y`
- `width` and `height` default to global tile size if omitted
- `frames` defaults to 1 if omitted
- `animation_fps` defaults to 10.0 if omitted

---

## Testing Requirements

### Unit Tests

**Required Coverage**:
- SpriteManager: 90%+ coverage
- ImageRenderer: 85%+ coverage
- Data loading: 95%+ coverage
- Utility functions: 100% coverage

**Test Files**:
```
tests/
  test_sprite_manager.py
  test_image_renderer.py
  test_render_mode.py
  test_sprite_metadata.py
```

### Integration Tests

**Scenarios**:
1. Load game in ASCII mode → Switch to sprite mode → Verify display
2. Load game in sprite mode → Switch to ASCII → Verify display
3. Missing sprite → Verify fallback to ASCII
4. Unsupported terminal → Verify auto-fallback
5. Save game in sprite mode → Load in ASCII mode → Verify compatibility

### Performance Tests

**Benchmarks**:
```python
def test_sprite_rendering_performance():
    """Sprite mode should maintain 30+ FPS."""
    fps = measure_fps_for_n_frames(1000)
    assert fps >= 30

def test_memory_usage():
    """Sprite cache should not exceed configured limit."""
    max_memory = measure_max_memory_mb()
    assert max_memory <= SPRITE_CACHE_SIZE_MB + 10  # 10MB tolerance
```

### Acceptance Tests

**User Stories**:
- As a user, I can toggle graphics mode in settings
- As a user, I see sprites when in sprite mode (if supported)
- As a user, I see ASCII when in ASCII mode or sprites unsupported
- As a user, my save files work in both modes
- As a user, I get clear feedback if sprite mode isn't available

---

## Security Considerations

### Image Loading

- Validate image file formats (PNG only)
- Limit max image dimensions (prevent memory exhaustion)
- Sanitize file paths (prevent directory traversal)
- Handle corrupt images gracefully

### Resource Limits

- Enforce sprite cache memory limit
- Prevent unbounded sprite sheet sizes
- Limit number of loaded sheets

---

## Migration Strategy

### Phase 1: Add Infrastructure (No User Impact)
- Add sprite management code
- Add config options (default to ASCII)
- Add data schema (optional fields)
- Deploy with feature flag disabled

### Phase 2: Beta Testing
- Enable feature flag for opt-in users
- Gather feedback and performance data
- Fix bugs, optimize

### Phase 3: General Availability
- Enable by default for capable terminals
- Provide fallback for others
- Monitor for issues

---

## Dependencies

### New Python Packages

```txt
Pillow>=10.0.0
```

### Asset Dependencies

- Sprite sheets (PNG format)
- Sprite metadata JSON
- Artist guidelines documentation

### Development Dependencies

```txt
pytest>=7.0.0
pytest-benchmark>=4.0.0
memory_profiler>=0.60.0
```

---

## Success Criteria

Implementation is complete when:

- [ ] All FR requirements met
- [ ] All NFR targets achieved
- [ ] Unit test coverage ≥85%
- [ ] Integration tests pass
- [ ] Performance tests pass
- [ ] Documentation complete
- [ ] User guide written
- [ ] Beta testing successful (no critical bugs)
- [ ] Sprite mode works in Kitty terminal
- [ ] ASCII mode unaffected (no performance regression)

---

## Open Questions

Document answers as implementation progresses:

1. **Should we support variable sprite sizes?**
   - Decision: TBD
   - Reasoning: TBD

2. **Should animated sprites be synchronized globally or per-entity?**
   - Decision: TBD
   - Reasoning: TBD

3. **How do we handle multi-tile entities (e.g., large dragons)?**
   - Decision: TBD
   - Reasoning: TBD

4. **Should we implement sprite color tinting for variants?**
   - Decision: TBD
   - Reasoning: TBD

---

## References

### External Documentation

- [Kitty Graphics Protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Textual Documentation](https://textual.textualize.io/)

### Internal Documentation

- `docs/IMAGE_SPRITE_ANALYSIS.md` - Feasibility analysis
- `docs/IMAGE_SPRITE_IMPLEMENTATION_PLAN.md` - Implementation roadmap
- `README.md` - Project overview

---

## Appendix A: Example Code

### Complete Sprite Rendering Example

```python
from app.lib.rendering.sprite_manager import SpriteManager
from app.lib.rendering.image_renderer import KittyImageRenderer
from app.lib.rendering.render_mode import RenderMode

# Initialize systems
sprite_mgr = SpriteManager(cache_size_mb=50)
sprite_mgr.load_metadata("data/sprite_metadata.json")
renderer = KittyImageRenderer()

# Check support
if not renderer.is_supported():
    print("Sprite mode not supported, using ASCII")
    render_mode = RenderMode.ASCII
else:
    render_mode = RenderMode.SPRITES

# Render viewport
if render_mode == RenderMode.SPRITES:
    sprites = []
    for y in range(viewport_height):
        row = []
        for x in range(viewport_width):
            # Get tile info from game engine
            tile = engine.get_tile(x, y)
            
            # Get sprite
            if tile.entity:
                sprite = sprite_mgr.get_entity_sprite(tile.entity.id)
            elif tile.item:
                sprite = sprite_mgr.get_item_sprite(tile.item.id)
            else:
                sprite = sprite_mgr.get_terrain_sprite(tile.char)
            
            row.append(sprite)
        sprites.append(row)
    
    # Composite and render
    viewport_img = renderer.composite_viewport(sprites, 16, 16)
    renderer.render_image(viewport_img, 0, 0, image_id=1)
```

---

## Appendix B: Kitty Protocol Reference

### Basic Image Display

```python
# Escape sequence format:
# \x1b_G<control data>;<base64 data>\x1b\\

# Example: Display inline image
escape = f"\x1b_Gf=100,i={image_id};{base64_png_data}\x1b\\"
sys.stdout.write(escape)
sys.stdout.flush()
```

### Control Data Keys

- `f=100`: Format (100 = PNG)
- `i=<id>`: Image ID
- `m=<0|1>`: More data coming (1) or last chunk (0)
- `a=T`: Transmission method (T = direct)
- `X=<col>`: Column position
- `Y=<row>`: Row position

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-10-28 | Copilot | Initial requirements document |

---

**Document Status**: Draft - For Review
