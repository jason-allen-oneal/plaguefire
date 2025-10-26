# Quick Reference - Implementation Status

This is a condensed view of the most important items from TODO.md.

## 🔴 User-Facing "Not Yet Implemented" (Fix First)

These show error messages to players when they try to use them:

1. **Aim/Zap Wand** - Line 637-640 in `app/screens/game.py`
2. **Use/Zap Staff** - Line 675-678 in `app/screens/game.py`
3. **Read Scroll** - Line 670-673 in `app/screens/game.py`
4. **Drop Item** - Line 647-650 in `app/screens/game.py`
5. **Fire/Throw** - Line 656-659 in `app/screens/game.py`

## 🟡 Infrastructure Built but Not Connected

These systems are complete with tests but not wired into gameplay:

1. **Item Instance Tracking**
   - File: `app/lib/core/item_instance.py`
   - Tests: ✅ 6/6 passing
   - Status: Not integrated into Player class

2. **Mining System**
   - File: `app/lib/core/mining_system.py`
   - Tests: ✅ 8/8 passing
   - Status: No mining command, veins not in dungeons

3. **Chest System**
   - File: `app/lib/core/chest_system.py`
   - Tests: ✅ 9/9 passing
   - Status: Chests not spawned, commands not wired

## 🟢 Equipment Slots Missing

Items exist in data but no slots to equip them:

- **Rings** (30 items defined) - Need ring_left, ring_right slots
- **Amulets** (9 items defined) - Need amulet slot
- **Shields** - Need shield slot

## 📊 By the Numbers

- **70** total TODO items identified
- **17** high priority (user-facing features)
- **8** medium priority (system integration)
- **45+** low priority (enhancements)
- **3** infrastructure systems ready to integrate
- **8/8** tests passing ✅

## 🎯 Fastest Path to Value

**Week 1**: Integrate ItemInstance into Player
- Enables charge tracking for wands/staves
- Enables {empty} and {tried} inscriptions
- Unlocks Aim Wand and Use Staff features

**Week 2**: Add equipment slots
- Ring slots (ring_left, ring_right)
- Amulet slot
- Shield slot
- Enables 69 items currently in data but unusable

**Week 3**: Wire up existing systems
- Add mining command (system already complete)
- Spawn chests in dungeons (system already complete)
- Connect chest interaction commands

**Week 4**: Core actions
- Drop Item (inventory management)
- Read Scroll (similar to existing potion system)
- Fire/Throw (projectile system)

## 📝 Files to Focus On

Most changes needed in these files:

1. `app/lib/generation/entities/player.py` - Add equipment slots, integrate ItemInstance
2. `app/screens/game.py` - Wire up action handlers
3. `app/lib/core/engine.py` - Add gameplay commands
4. `app/lib/generation/maps/generate.py` - Add chest spawning

## ⚠️ Known Stubs

Only 3 genuine pass statements (with comments):
- `player.py:1098` - Charge tracking (needs ItemInstance integration)
- `engine.py:372` - Book consumption policy decision
- `item_instance.py:53` - Charge init (appropriate)

---

For full details, see:
- `TODO.md` - Complete list with 70 items
- `REVIEW_SUMMARY.md` - Detailed findings
- `EXTREME_REFACTORS.md` - Infrastructure implementation details
