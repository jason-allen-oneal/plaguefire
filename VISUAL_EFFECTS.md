# Visual Effects System

This document describes the visual effects system added to Plaguefire, including projectile animations, item physics, and ammo recovery.

## Features

### 1. Projectile System

Visual projectiles are now rendered when:
- Casting attack spells (e.g., Magic Missile, Fire Bolt)
- Throwing items (daggers, potions, arrows)
- Monster ranged attacks (planned for future)

**Implementation:**
- `Projectile` class in `app/lib/core/projectile.py`
- Uses Bresenham's line algorithm for smooth paths
- Color-coded by projectile type (magic, arrow, fire, ice, etc.)
- Animated at ~20 FPS (0.05s per step)

**Example:**
```python
# Add a projectile from player to target
engine.add_projectile((px, py), (tx, ty), '*', 'magic')
```

### 2. Item Physics

Dropped items now use physics simulation to "roll" across the floor:
- Items have velocity and friction
- They roll to a final position over several animation frames
- Walls and map boundaries are respected
- Items find nearest valid floor tile if they roll out of bounds

**Implementation:**
- `DroppedItem` class in `app/lib/core/projectile.py`
- Physics updated each turn
- Friction coefficient: 0.85 (items slow down gradually)
- Maximum animation steps: 20

**Triggers:**
- Dropping items from inventory (d key)
- Entity death (monsters drop loot)
- Failed item pickups

**Example:**
```python
# Drop item with physics
engine.add_dropped_item_with_physics("Sword", (x, y), velocity=(1.0, 0.5))
```

### 3. Ammo Recovery System

Ammunition (arrows, bolts, darts, javelins) can now be recovered after use:

**Recovery Rates:**
- **Clean miss** (no target hit): 90% recovery chance
- **Miss target** (target present but missed): 80% recovery chance
- **Hit target**: 50% recovery chance

**Implementation:**
- Ammo detection: Keywords "Arrow", "Bolt", "Dart", "Javelin"
- Recovery logic in `handle_throw_item()`
- Recovered ammo appears on ground at impact location

**Benefits:**
- Makes ranged combat more sustainable
- Rewards careful play (missing is better than hitting when conserving ammo)
- Adds tactical depth (retrieve ammo after battle)

## Visual Rendering

Projectiles and animating items are rendered in the `DungeonView`:

1. **Projectiles**: Displayed with color based on type
   - Magic spells: magenta `*`
   - Arrows/bolts: yellow `/`
   - Fire: red `*`
   - Ice: bright cyan `*`

2. **Animating items**: Displayed as yellow `*` while rolling

3. **Animation**: Automatic via interval timer (0.05s refresh)

## Code Architecture

### Core Classes

**`Projectile`** (`app/lib/core/projectile.py`)
- Stores start/end positions and path
- Advances through path step by step
- Provides color-coded character for rendering

**`DroppedItem`** (`app/lib/core/projectile.py`)
- Simulates 2D physics with velocity and friction
- Settles when velocity is very low
- Returns final position for ground placement

### Engine Integration

**`Engine`** (`app/lib/core/engine.py`)
- `active_projectiles`: List of animating projectiles
- `dropped_items`: List of items in physics simulation
- `add_projectile()`: Create new projectile
- `update_dropped_items()`: Update physics each turn
- `clear_inactive_projectiles()`: Clean up finished animations

### View Integration

**`DungeonView`** (`app/ui/dungeon_view.py`)
- Animation timer: Updates every 0.05s
- `_animate_projectiles()`: Advances all projectiles
- Renders projectiles and animating items in `update_map()`

## Testing

### Unit Tests

**`test_projectile_system.py`** (8 tests)
- Projectile creation and path calculation
- Path advancement
- Color coding
- Dropped item physics
- Friction simulation
- Item settling

### Integration Tests

**`test_visual_effects_integration.py`** (5 tests)
- Spell projectile creation
- Thrown item projectiles
- Ammo recovery mechanics
- Item drop physics
- Entity death item physics

### Updated Tests

**`test_ground_items.py`**
- Updated to account for physics simulation delay

**`test_high_priority_todos.py`**
- Updated drop_item test for physics

## Performance Considerations

- Projectiles are cleaned up automatically when animation completes
- Physics simulation runs only while items are animating
- Maximum 20 steps per item prevents infinite animations
- Bounds checking prevents out-of-map issues

## Future Enhancements

Possible improvements for the future:

1. **Particle Effects**: Add particle trails for spells
2. **Monster Projectiles**: Extend to monster ranged attacks
3. **Impact Effects**: Visual feedback on hit/miss
4. **Configurable Speed**: Allow adjusting animation speed
5. **Sound Effects**: Add sounds for projectile impacts
6. **Area Effects**: Visual representation of area spells
7. **Bounce Physics**: Items bounce off walls
8. **Varied Friction**: Different items have different friction

## Usage Examples

### Casting a Spell
```python
# In cast_spell screen, when targeting an enemy
engine.handle_cast_spell("magic_missile", target_entity)
# Creates projectile automatically
```

### Throwing an Item
```python
# In throw_item screen, after selecting item and direction
engine.handle_throw_item(item_index, dx=1, dy=0)
# Creates projectile and handles recovery
```

### Dropping an Item
```python
# In inventory/drop screen
engine.handle_drop_item(item_index)
# Item rolls to final position with physics
```

### Checking for Ammo on Ground
```python
# After battle, look for recoverable ammo
pos_key = (x, y)
if pos_key in engine.ground_items:
    for item in engine.ground_items[pos_key]:
        if "Arrow" in item or "Bolt" in item:
            # Ammo can be picked up
            engine.handle_pickup_item()
```

## Configuration

Currently, physics parameters are hardcoded but could be made configurable:

```python
# In DroppedItem class
friction = 0.85          # How quickly items slow down (0-1)
max_steps = 20          # Maximum animation duration
settle_threshold = 0.1   # Velocity below which item settles

# In DungeonView
animation_interval = 0.05  # Seconds between animation frames
```

## Compatibility

- Works with existing save game system
- Compatible with all item types
- No changes to data files required
- Backward compatible with existing gameplay

## Known Limitations

1. Projectiles are visual only - damage is calculated immediately
2. Physics is 2D only (no height/gravity)
3. Items can't stack during physics (each animates separately)
4. No collision between multiple dropped items

These limitations could be addressed in future updates if needed.
